import os

from pycocotools.coco import COCO
import pycocotools.mask as maskUtils
import json
from copy import deepcopy
import numpy as np


def ann2mask(mask_ann, img_h, img_w):
    """Private function to convert masks represented with polygon to
    bitmaps.

    Args:
        mask_ann (list | dict): Polygon mask annotation input.
        img_h (int): The height of output mask.
        img_w (int): The width of output mask.

    Returns:
        numpy.ndarray: The decode bitmap mask of shape (img_h, img_w).
    """

    if isinstance(mask_ann, list):
        # polygon -- a single object might consist of multiple parts
        # we merge all parts into one mask rle code
        rles = maskUtils.frPyObjects(mask_ann, img_h, img_w)
        rle = maskUtils.merge(rles)
    elif isinstance(mask_ann['counts'], list):
        # uncompressed RLE
        rle = maskUtils.frPyObjects(mask_ann, img_h, img_w)
    else:
        # rle
        rle = mask_ann
    mask = maskUtils.decode(rle)
    return mask


def mask2rle(mask):
    """
    mask: np.array((h, w), dtype=np.bool)
    {"segmentation": ins_mask_rle} can used save into json file
    """
    if len(mask.shape) == 2:
        mask = mask[:, :, np.newaxis]
    elif len(mask.shape) == 3:
        assert mask.shape[2] == 1
    else:
        raise ValueError
    ins_mask_rle = maskUtils.encode(np.array(mask, order='F', dtype='uint8'))[0]  # encoded with RLE
    if isinstance(ins_mask_rle['counts'], bytes):
        ins_mask_rle['counts'] = ins_mask_rle['counts'].decode()
    return ins_mask_rle


def filter_small_bbox(coco_anno, min_size=2):
    new_anno = []
    for anno in coco_anno["annotations"]:
        box = anno["bbox"]
        #         if box[2] * box[3] >= min_size * min_size:
        if box[2] >= min_size and box[3] >= min_size:
            new_anno.append(anno)
    coco_anno['annotations'] = new_anno


def filter_ignore_uncertain_bbox(coco_anno):
    new_anno = []
    for anno in coco_anno["annotations"]:
        if ("ignore" in anno and anno["ignore"]) or \
                ("uncertain" in anno and anno["uncertain"]):
            continue
        new_anno.append(anno)
    coco_anno['annotations'] = new_anno


def img_id2info(coco_annos):
    id2info = {}
    for img_info in coco_annos['images']:
        id2info[img_info['id']] = img_info
    return id2info


def clip_to_image(coco_anno):
    iid2info = img_id2info(coco_anno)
    for anno in coco_anno["annotations"]:
        info = iid2info[anno['image_id']]
        W, H = info['width'], info['height']
        x1, y1, w, h = anno['bbox']
        x2 = x1 + w - 1
        y2 = y1 + h - 1
        x1, x2 = [min(max(0, x), W - 1) for x in [x1, x2]]
        y1, y2 = [min(max(0, y), H - 1) for y in [y1, y2]]
        w = x2 - x1 + 1
        h = y2 - y1 + 1
        anno['bbox'] = [x1, y1, w, h]


def seg_to_polygon(segm):
    if type(segm) == list:
        return segm
    elif type(segm['counts']) == list:
        # uncompressed RLE
        h, w = segm['size']
        rle = maskUtils.frPyObjects(segm, h, w)
    else:
        # rle
        rle = segm
    mask = maskUtils.decode(rle)

    from huicv.deps.pycococreatortools import binary_mask_to_polygon
    return binary_mask_to_polygon(mask)


def dump_coco_annotation(jd, save_path, n_round=3):
    if 'annotations' in jd:
        for ann in jd['annotations']:
            if 'bbox' in ann:
                ann['bbox'] = np.array(ann['bbox']).round(n_round).tolist()
            if 'point' in ann:
                ann['point'] = np.array(ann['point']).round(n_round).tolist()
            if 'segmentation' in ann:
                if isinstance(ann['segmentation'], list):
                    for i, seg in enumerate(ann['segmentation']):
                        ann['segmentation'][i] = np.array(seg).round(n_round).tolist()
            if 'area' in ann:
                ann['area'] = round(ann['area'], n_round)
    json.dump(jd, open(save_path, 'w'), separators=(',', ':'))


class GCOCO(COCO):
    """
    images:
        {
         'license': 4,
         'file_name': '000000397133.jpg',
         'coco_url': 'http://images.cocodataset.org/val2017/000000397133.jpg',
         'height': 427,
         'width': 640,
         'date_captured': '2013-11-14 17:02:52',
         'flickr_url': 'http://farm7.staticflickr.com/6116/6255196340_da26cf2c9e_z.jpg',
         'id': 397133
        }
    """
    def __init__(self, *args, **kwargs):
        super(GCOCO, self).__init__(*args, **kwargs)
        self.oriImgs = self.imgs
        self.oriImgToAnns = self.imgToAnns

        for ann in self.anns.values():
            ann['ignore'] = ann.get("ignore", False) or ann.get("iscrowd", False)

        self.CLASSES = [cat['name'] for cat in self.dataset['categories']]
        self.cat_ids = self.get_cat_ids(cat_names=self.CLASSES)
        self.cat2label = {cat_id: i for i, cat_id in enumerate(self.cat_ids)}

    def get_cat_ids(self, cat_names=[], sup_names=[], cat_ids=[]):
        return self.getCatIds(cat_names, sup_names, cat_ids)

    @staticmethod
    def group_by_cat_id(anns):
        """Get COCO category ids by index.

        Args:
            idx (int): Index of data.

        Returns:
            list[int]: All categories in the image of specified index.
        """
        cid2anns = {}
        for ann in anns:
            cid = ann['category_id']
            if cid not in cid2anns:
                cid2anns[cid] = [ann]
            else:
                cid2anns[cid].append(ann)
        return cid2anns

    def area_of_seg_use_img_size(self, ann):
        """
        depend on 'width' and 'height' in image info of 'images', do not change them before call it.
        """
        rle = self.annToRLE(ann)
        return maskUtils.area(rle)

    def save(self, path, min_size=2, n_round=3):
        os.makedirs(os.path.split(path)[0], exist_ok=True)
        clip_to_image(self.dataset)
        filter_small_bbox(self.dataset, min_size=min_size)
        dump_coco_annotation(self.dataset, path, n_round)

    def resize_ann(self, ann, ws, hs, area_use='bbox', inplace=False, ignore_rle=False):
        def resize_xy_list(xy_list, ss):
            assert len(xy_list) % 2 == 0
            points = np.array(xy_list).reshape(-1, 2)
            # print(xy_list, ann['bbox'], 2*n, points.shape)
            xy_list = (points * ss).reshape(-1,).tolist()
            return xy_list

        if not inplace:
            ann = deepcopy(ann)

        ss = np.array([[ws, hs]])
        ann['bbox'] = resize_xy_list(ann['bbox'], ss)

        # resize segmentation
        segmentation = ann['segmentation'] if ignore_rle else seg_to_polygon(ann['segmentation'])
        if isinstance(segmentation, list):
            # print('s list', ann['id'], ann['image_id'], len(ann['segmentation']))
            ann['segmentation'] = [resize_xy_list(seg_part, ss) for i, seg_part in enumerate(segmentation)]

        # 'area' is area of segmentation mask in 1x by default
        if area_use == 'bbox':
            ann['area'] = ann["bbox"][-1] * ann["bbox"][-2]
        elif area_use == "segmentation":
            # ann['area'] = dataset.area_of_seg_use_img_size(ann)
            raise NotImplementedError
        else:
            raise ValueError
        return ann

    @staticmethod
    def translate_ann(ann, dx, dy, inplace=False):
        def translate_xy_list(xy_list, d):
            assert len(xy_list) % 2 == 0
            points = np.array(xy_list).reshape((-1, 2))
            xy_list = (points + d).reshape((-1,)).tolist()
            return xy_list

        if not inplace:
            ann = deepcopy(ann)

        d = np.array([[dx, dy]])
        ann['bbox'][:2] = translate_xy_list(ann['bbox'][:2], d)

        # resize segmentation
        segmentation = seg_to_polygon(ann['segmentation'])
        assert isinstance(segmentation, list)
        # print('s list', ann['id'], ann['image_id'], len(ann['segmentation']))
        ann['segmentation'] = [translate_xy_list(seg_part, d) for i, seg_part in enumerate(segmentation)]
        return ann

    # overwrite
    def showAnns(self, anns, draw_bbox=False, draw_point=False, drwa_image=False, img_root=""):
        """
            Display the specified annotations.
            :param anns (array of object): annotations to display
            :return: None
        """
        import matplotlib.pyplot as plt
        from matplotlib.collections import PatchCollection
        from matplotlib.patches import Polygon

        if len(anns) == 0:
            return 0

        if drwa_image:
            assert len(set([ann['image_id'] for ann in anns])) == 1
            import os
            from PIL import Image
            img_path = os.path.join(img_root, self.imgs[anns[0]['image_id']]['file_name'])
            img = np.array(Image.open(img_path))
            plt.imshow(img)

        if 'segmentation' in anns[0] or 'keypoints' in anns[0]:
            datasetType = 'instances'
        elif 'caption' in anns[0]:
            datasetType = 'captions'
        else:
            raise Exception('datasetType not supported')
        if datasetType == 'instances':
            ax = plt.gca()
            ax.set_autoscale_on(False)
            polygons = []
            color = []
            for ann in anns:
                c = (np.random.random((1, 3)) * 0.6 + 0.4).tolist()[0]
                if 'segmentation' in ann:
                    if type(ann['segmentation']) == list:
                        # polygon
                        for seg in ann['segmentation']:
                            poly = np.array(seg).reshape((int(len(seg) / 2), 2))
                            polygons.append(Polygon(poly))
                            color.append(c)
                    else:
                        # mask
                        t = self.imgs[ann['image_id']]
                        if type(ann['segmentation']['counts']) == list:
                            rle = maskUtils.frPyObjects([ann['segmentation']], t['height'], t['width'])
                        else:
                            rle = [ann['segmentation']]
                        m = maskUtils.decode(rle)
                        img = np.ones((m.shape[0], m.shape[1], 3))
                        if ann['iscrowd'] == 1:
                            color_mask = np.array([2.0, 166.0, 101.0]) / 255
                        if ann['iscrowd'] == 0:
                            color_mask = np.random.random((1, 3)).tolist()[0]
                        for i in range(3):
                            img[:, :, i] = color_mask[i]
                        ax.imshow(np.dstack((img, m * 0.5)))
                if 'keypoints' in ann and type(ann['keypoints']) == list:
                    # turn skeleton into zero-based index
                    sks = np.array(self.loadCats(ann['category_id'])[0]['skeleton']) - 1
                    kp = np.array(ann['keypoints'])
                    x = kp[0::3]
                    y = kp[1::3]
                    v = kp[2::3]
                    for sk in sks:
                        if np.all(v[sk] > 0):
                            plt.plot(x[sk], y[sk], linewidth=3, color=c)
                    plt.plot(x[v > 0], y[v > 0], 'o', markersize=8, markerfacecolor=c, markeredgecolor='k',
                             markeredgewidth=2)
                    plt.plot(x[v > 1], y[v > 1], 'o', markersize=8, markerfacecolor=c, markeredgecolor=c,
                             markeredgewidth=2)

                if draw_bbox:
                    [bbox_x, bbox_y, bbox_w, bbox_h] = ann['bbox']
                    poly = [[bbox_x, bbox_y], [bbox_x, bbox_y + bbox_h], [bbox_x + bbox_w, bbox_y + bbox_h],
                            [bbox_x + bbox_w, bbox_y]]
                    np_poly = np.array(poly).reshape((4, 2))
                    polygons.append(Polygon(np_poly))
                    color.append(c)
                if draw_point:
                    x, y = ann['point']
                    ax.scatter(x, y, color=c)

            p = PatchCollection(polygons, facecolor=color, linewidths=0, alpha=0.4)
            ax.add_collection(p)
            p = PatchCollection(polygons, facecolor='none', edgecolors=color, linewidths=2)
            ax.add_collection(p)

            return color  # add by hui
        elif datasetType == 'captions':
            for ann in anns:
                print(ann['caption'])


import os
import numpy as np
from PIL import Image
import matplotlib.pyplot as plt


class COCOVisUtils(object):
    # def __init__(self, coco):
    #     if isinstance(coco, str):
    #         coco = COCO(coco)
    #     elif isinstance(coco, COCO):
    #         pass
    #     else:
    #         raise TypeError
    #     self.coco = coco

    @staticmethod
    def load_image(img_info, data_root='data/coco/images/', dtype=np.float32):
        img = Image.open(os.path.join(data_root, img_info['file_name']))
        if dtype == np.float32:
            img = np.array(img).astype(np.float32) / 255
        return img

    @staticmethod
    def show_image(img_info, data_root='data/coco/images/', dtype=np.float32):
        img = COCOVisUtils.load_image(img_info, data_root, dtype)
        plt.imshow(img)

    @staticmethod
    def draw_anns(gt_anns, key='bbox', cat_ids=None, ax=None, linewidth=3):
        if ax is None:
            ax = plt.gca()
        if cat_ids is not None:
            gt_anns = [ann for ann in gt_anns if ann['category_id'] in cat_ids]

        # draw bboxes
        for gt_ann in gt_anns:
            bbox = gt_ann[key]
            ax.add_patch(
                plt.Rectangle((bbox[0], bbox[1]), bbox[2], bbox[3], color="#009e73", fill=False, linewidth=linewidth,
                              linestyle='dashed'))

    @staticmethod
    def draw_dets(dets, cat_ids=None, ax=None, linewidth=3):
        raise NotImplemented

    @staticmethod
    def show_image_with_anns(coco, img_id=None, data_root='data/coco/images/', show=True):
        if img_id is None:
            img_id = list(coco.imgs.keys())[0]
        img_info = coco.imgs[img_id]
        COCOVisUtils.show_image(img_info, data_root)

        anns = coco.loadAnns(coco.getAnnIds(imgIds=[img_id]))
        COCOVisUtils.draw_anns(anns, 'bbox')
        if show:
            plt.show()

    @staticmethod
    def get_cat_id(cat_name, coco):
        for cat_id, cat in coco.cats:
            if cat['name'] == cat_name:
                return cat_id


if __name__ == '__main__':
    from pycocotools.coco import COCO

    coco = COCO('data/coco/annotations/val2017.json')
    coco_vis = COCOVisUtils()
    # img_id=None means show the first image in coco.imgs
    coco_vis.show_image_with_anns(coco, img_id=None, data_root='data/coco/train2017/')
