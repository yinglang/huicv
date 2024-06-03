from PIL import Image
import matplotlib.pyplot as plt
from tqdm import tqdm
import numpy as np
import os
from .common_utils import *


def filter_image_ids(coco, image_number_or_ids):
    if isinstance(image_number_or_ids, int):
        image_ids = list(coco.imgs.keys())[:image_number_or_ids]
    elif isinstance(image_number_or_ids, (tuple, list)):
        image_ids = image_number_or_ids
    elif image_number_or_ids is None:
        image_ids = list(coco.imgs.keys())
    else:
        raise ValueError()
    return image_ids


def show_image_set_with_results(coco, img_results, image_dir, save_dir=None, image_number_or_ids=None,
                                score_thr=0.3, class_names=None, fontsize=10, linewidth=2, skip_exists=False,
                               ):
    """ show or save image set with give results
    Args:
        coco: pycocotools.coco.COCO
        img_results: dict
            {
                img_id: [
                    [x1, y1, x2, y2, label, score],
                    ...
                ]
                ...
            }
        image_dir: str, relative dir for img_info['file_name']
        save_dir: str, if is None means show image and not save, if not None means save and not show image.
        
    Example:
        # show images specified by $image_number_or_ids
        show_image_set_with_results(coco, save_results, image_dir, image_number_or_ids=3, score_thr=0.3, class_names=id2name)
        # save all images with results to $save_dir
        show_image_set_with_results(coco, save_results, image_dir, save_dir, score_thr=0.3, class_names=id2name)
    """
    image_ids = filter_image_ids(coco, image_number_or_ids)
       
    for img_id in tqdm(image_ids):
        img_info = coco.imgs[img_id]
        img_path = os.path.join(image_dir, img_info['file_name'])
        save_path = os.path.join(save_dir, img_info['file_name']) if save_dir is not None else None
        if skip_exists and save_path and os.path.exists(save_path):
            continue

        # load result
        if img_id not in img_results:
            print(f"[warning]: det results of {img_id} not in saved results")
            results = np.zeros((0, 6))
        else:
            results = img_results[img_id]
            # print(res.keys())
            if results.shape[-1] >= 6:  # have scores
                results = results[results[:, 5]>score_thr]

        # plot or save image with results
        try:
            image = Image.open(img_path)
        except Exception as e:
            print(e, f"error while load {img_path}")
            continue
        show_image_with_det_results(
            image, results, save_path, 
            show_text=True, class_names=class_names, 
            fontsize=fontsize, linewidth=linewidth)

        # show image is not save
        if save_dir is None:
            plt.show()
        plt.clf()
        plt.close()


def show_image_set_with_anns(coco, *args, image_number_or_ids=None, **kwargs,
                               ):
    """ show or save image set with give anns, details see """
    image_ids = filter_image_ids(coco, image_number_or_ids)
    img_results = {img_id: anns_to_results(coco.imgToAnns[img_id]) for img_id in image_ids}
    return show_image_set_with_results(coco, img_results, *args, image_number_or_ids=image_ids, **kwargs)
