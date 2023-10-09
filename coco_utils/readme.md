## resize_dataset

```shell
# COCO200, train+val
PYTHONPATH=..:$PYTHONPATH python ../huicv/coco_utils/resize_dataset.py \
  data/coco/annotations/instances_train2017.json data/coco/images \
  --save-ann data/coco/resize/annotations/instances_train2017_200x333.json \
  --save-img-root data/coco/resize/images_200x333_q100 --im-size 200,333 --jpg-quality 100
PYTHONPATH=..:$PYTHONPATH python ../huicv/coco_utils/resize_dataset.py \
  data/coco/annotations/instances_val2017.json data/coco/images \
  --save-ann data/coco/resize/annotations/instances_val2017_200x333.json \
  --save-img-root data/coco/resize/images_200x333_q100 --im-size 200,333 --jpg-quality 100
```

## 1. show image of coco format dataset
```python
from pycocotools.coco import COCO
from huicv.coco_utils.coco_ann_utils import COCOVisUtils
coco = COCO('data/coco/annotations/val2017.json')
coco_vis = COCOVisUtils()
# img_id=None means show the first image in coco.imgs
coco_vis.show_image_with_anns(coco, img_id=None, data_root='data/coco/train2017')
```