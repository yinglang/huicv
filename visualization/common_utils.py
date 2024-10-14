import numpy as np
import matplotlib.pyplot as plt
from copy import deepcopy


def show_images(imgs, plot_func=None, mxn=None, fig_kwargs={}, titles=None, show=True):
    if mxn is None:
        m = int(np.round(np.sqrt(len(imgs))))
        n = int(np.ceil(len(imgs) / m))
        mxn = (m, n)
    num_rows, num_cols = mxn
    if 'figsize' not in fig_kwargs:
        fig_kwargs = deepcopy(fig_kwargs)
        W = max([sum([img.shape[1] for img in imgs[i*num_cols:(i+1)*num_cols]]) for i in range(num_rows)])
        H = max([sum([img.shape[0] for img in imgs[j::num_cols]]) for j in range(num_cols)])
        fig_kwargs['figsize'] = (int(W/100), int(H/100))  # dpi=100
    fig, axes = plt.subplots(num_rows, num_cols, **fig_kwargs)  # figsize=(4, 3)
    for i in range(num_rows):
        for j in range(num_cols):
            idx = i * num_cols + j
            # 获取当前子图的坐标轴
            if not hasattr(axes, 'shape'):
                ax = axes
            elif len(axes.shape) == 2:
                ax = axes[i, j]
            elif len(axes.shape) == 1:  # num_rows = 1 or num_cols = 1
                ax = axes[idx]
            else:
                raise ValueError

            if idx < len(imgs):
                ax.imshow(imgs[idx])
                if plot_func is not None:
                    plot_func(idx, ax)
                if titles is not None:
                    ax.set_title(titles[idx])
            else:
                plt.delaxes(ax)
    # 调整子图之间的间距
    plt.tight_layout()
    if show:
        plt.show()


import numpy as np
import matplotlib.pyplot as plt
import warnings
from .bbox_utils import *
import numpy as np


def draw_a_bbox(box, color, linewidth=1, dash=False, fill=False, ax=None):
    if ax is None:
        ax = plt.gca()
    if dash:
        # box_to_dashed_rect(plt, box, color, linewidth)
        ax.add_patch(box_to_rect(box, color, linewidth, fill=fill, ls='--'))
    else:
        ax.add_patch(box_to_rect(box, color, linewidth, fill=fill))


def box_to_dashed_rect(box, color, linewidth=1, ax=None):
    if ax is None:
        ax = plt.gca()
    x1, y1, x2, y2 = box
    ax.plot([x1, x2], [y1, y1], '--', color=color, linewidth=linewidth)
    ax.plot([x1, x2], [y2, y2], '--', color=color, linewidth=linewidth)
    ax.plot([x1, x1], [y1, y2], '--', color=color, linewidth=linewidth)
    ax.plot([x2, x2], [y1, y2], '--', color=color, linewidth=linewidth)


def box_to_rect(box, color, linewidth=1, fill=False, ls='-'):
    """convert an anchor box to a matplotlib rectangle"""
    alpha = 0.2 if fill else None
    return plt.Rectangle((box[0], box[1]), box[2]-box[0], box[3]-box[1],
                  fill=fill, alpha=alpha, edgecolor=color, facecolor=color,
                  linewidth=linewidth, linestyle=ls)


def draw_bbox(fig, bboxes, color=None, linewidth=1, fontsize=5, normalized_label=False, wh=None,
              show_text=False, class_names=None, class_colors=None, use_real_line=None, threshold=None):
    """
        draw boxes on fig
    argumnet:
        bboxes: [[x1, y1, x2, y2, (cid), (score), (ann_id) ...]],
        color: box color, if class_colors not None, it will not use.
        normalized_label: if label xmin, xmax, ymin, ymax is normaled to 0~1, set it to True and wh must given, else set to False.
        wh: (image width, height) needed when normalized_label set to True
        show_text: if boxes have cid or (cid, score) dim, can set to True to visualize it.
        use_real_line: None means all box use real line to draw, or [boolean...] means whether use real line for per class label.
        class_names: class name for every class.
        class_colors: class gt box color for every class, if set, argument 'color' will not use
    """
    if len(bboxes) == 0: return
    if np.max(bboxes) <= 1.:
        if normalized_label == False: warnings.warn(
            "[draw_bbox]:the label boxes' max value less than 1.0, may be it is noramlized box," +
            "maybe you need set normalized_label==True and specified wh", UserWarning)
    else:
        if normalized_label == True: warnings.warn(
            "[draw_bbox]:the label boxes' max value bigger than 1.0, may be it isn't noramlized box," +
            "maybe you need set normalized_label==False.", UserWarning)

    if normalized_label:
        assert wh != None, "wh must be specified when normalized_label is True. maybe you need setnormalized_label=False "
        bboxes = inv_normalize_box(bboxes, wh[0], wh[1])

    if color is not None and class_colors is not None:
        warnings.warn("'class_colors' set, then 'color' will not use, please set it to None")
    if color is None and class_colors is None:
        default_colors = plt.rcParams['axes.prop_cycle'].by_key()['color']
        class_colors = default_colors
        color = (0, 0, 0)
    instance_colors = None
    if color is not None:
        if isinstance(color[0], (tuple, list)):
            instance_colors = color
            color = None

    for i, box in enumerate(bboxes):
        if instance_colors is not None:
            color = instance_colors[i % len(instance_colors)]
        # [x1, y1, x2, y2, (cid), (score) ...]
        if len(box) >= 5 and box[4] < 0: continue  # have cid or not
        if len(box) >= 6 and threshold is not None and box[5] < threshold: continue
        if len(box) >= 5 and class_colors is not None: 
            cid = int(box[4])
            color = class_colors[cid % len(class_colors)]
            if cid >= len(class_colors):
                warnings.warn(f"class id {cid} is out of range of class_colors, need specified class_colors to a list with "
                              f"length bigger than {cid+1}, or class_colors[{cid} % {len(class_colors)}]")
        if len(box) >= 5 and use_real_line is not None and not use_real_line[int(box[4])]:
            box_to_dashed_rect(box[:4], color, linewidth, ax=fig)
        else:
            rect = box_to_rect(box[:4], color, linewidth)
            fig.add_patch(rect)
        if show_text:
            cid = int(box[4])
            if class_names is not None: cid = class_names[cid]
            text = str(cid)
            if len(box) >= 6 and box[5] >= 0: text += " {:.3f}".format(box[5])  # score
            if len(box) >= 7 and box[6] >= 0: text += " {}".format(int(box[6]))      # ann_id
            text_xy = (box[0], box[1])
            # text_xy = (box[0]+box[2]) / 2, (box[1]+box[3]) / 2
            fig.text(text_xy[0], text_xy[1], text,
                     bbox=dict(facecolor=(1, 1, 1), alpha=0.5), fontsize=fontsize, color=color)


def draw_center(ax, bboxes, **kwargs):
    center = np.array([((x1+x2)/2, (y1+y2)/2)for x1, y1, x2, y2, *arg in bboxes])
    ax.scatter(center[:, 0], center[:, 1], **kwargs)


def get_hsv_colors(n):
    import colorsys
    rgbs = [None] * n
    for i in range(n):
        h = i / n
        rgbs[i] = colorsys.hsv_to_rgb(h, 1, 1)
    return rgbs


# for coco annotation
def show_anns(anns, color=(0, 0, 0), axes=None):
    if axes is None:
        axes = plt.gca()
    bboxes = np.array([ann['bbox'] for ann in anns])
    bboxes = xywh2xyxy(bboxes)
    draw_bbox(axes, bboxes, color=color, normalized_label=False)


# function for show image with results
from PIL import Image
import os


def show_image_with_det_results(img_path, results, save_path=None, dpi=100, **kwargs):
    """
        img_path: str, PIL.ImageFile
        results: numpy.array, shape=(M, k)
            [
                [x1, y1, x2, y2, label, score],
                ...
            ]
        save_path: str

    Example:
        show_image_with_det_results(img_path, results, save_path, class_names=id2name, show_text=True, fontsize=15, linewidth=3)  
    """
    if isinstance(img_path, str):
        image = Image.open(img_path)
    else:
        image = img_path
        
    # print(, image.height)
    fig = plt.figure(figsize=(image.width//dpi, image.width//dpi), dpi=dpi)
    plt.imshow(image)
    plt.axis('off')  # 关闭坐标轴
    draw_bbox(fig.get_axes()[0], results, **kwargs)
    if save_path is not None:
        os.makedirs(os.path.split(save_path)[0], exist_ok=True)
        plt.margins(0, 0)
        plt.savefig(save_path, bbox_inches='tight', dpi=dpi, pad_inches=0.0)


def show_image_with_anns(img_path, anns, *args, **kwargs):
    kwargs = deepcopy(kwargs)
    show_ann_id = kwargs.pop("show_ann_id", False)
    return show_image_with_det_results(img_path, anns_to_results(anns, show_ann_id), *args, **kwargs)


def show_coco_image_with_ids(coco, image_dir, img_id=None, ann_id=None, anns=None, class_names=None, show_text=True, fontsize=10, **kwargs):
    """
    Example:
        show_coco_image_with_ids(coco_gt, image_dir, img_id=1)
        show_coco_image_with_ids(coco_gt, image_dir, ann_id=1)
        show_coco_image_with_ids(coco_gt, image_dir, ann_id=[1, 2, 3])
    """
    assert sum([img_id is not None, ann_id is not None, anns is not None]) == 1, "img_id, ann_id, anns must have one and only one"
    if ann_id is not None or anns is not None:
        if ann_id is not None:
            if not isinstance(ann_id, (tuple, list)):
                ann_id = [ann_id]
            assert len(ann_id) > 0, "ann_id is empty list"
            anns = [coco.anns[aid] for aid in ann_id]
        elif anns is not None:
            pass
        img_id = set([ann['image_id'] for ann in anns])
        assert len(img_id) == 1, "ann_id must belong to the same image, but img_id is {}".format(img_id)
        img_id = img_id.pop()
    elif img_id is not None:
        anns = coco.imgToAnns[img_id]
    else:
        raise ValueError()
        
    img_info = coco.imgs[img_id]
    img_path = os.path.join(image_dir, img_info['file_name'])
    if class_names is None:
        class_names = {cat_id: cat['name'] for cat_id, cat in coco.cats.items()}
    show_image_with_anns(img_path, anns, class_names=class_names, show_text=show_text, fontsize=fontsize, **kwargs)


# show with anns, anns to results
def anns_to_results(anns, show_ann_id=False):
    results = []
    for ann in anns:
        x1, y1, w, h = ann['bbox']
        x2, y2 = x1 + w, y1 + h
        res = [x1, y1, x2, y2, ann['category_id']]
        if show_ann_id:
            res.extend([-1, ann['id']])  # score, ann_id
        results.append(res)
    return np.array(results)
