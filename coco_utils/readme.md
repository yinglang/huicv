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
from huicv.coco_utils.coco_ann_utils import COCOVisUtils
from pycocotools.coco import COCO
import matplotlib.pyplot as plt

coco_vis = COCOVisUtils()
coco = COCO('data/coco/annotations/val2017.json')
img_id = list(coco.imgs.keys())[0]
coco_vis.show_image_with_anns(coco, img_id, data_root='data/coco/train2017/')
plt.show()

```