import numpy as np

def insect_boxes(box1, boxes):
    sx1, sy1, sx2, sy2 = box1[:4]
    tx1, ty1, tx2, ty2 = boxes[:, 0], boxes[:, 1], boxes[:, 2], boxes[:, 3]
    ix1 = np.where(tx1 > sx1, tx1, sx1)
    iy1 = np.where(ty1 > sy1, ty1, sy1)
    ix2 = np.where(tx2 < sx2, tx2, sx2)
    iy2 = np.where(ty2 < sy2, ty2, sy2)
    return np.array([ix1, iy1, ix2, iy2]).transpose((1, 0))


def bbox_area(boxes):
    s = np.zeros(shape=(boxes.shape[0],), dtype=np.float32)
    tx1, ty1, tx2, ty2 = boxes[:, 0], boxes[:, 1], boxes[:, 2], boxes[:, 3]
    h = (tx2 - tx1)
    w = (ty2 - ty1)
    valid = np.all(np.array([h > 0, w > 0]), axis=0)
    s[valid] = (h * w)[valid]
    return s


def bbox_iod(dets, gts, eps=1e-12):
    iods = np.zeros(shape=(dets.shape[0], gts.shape[0]), dtype=np.float32)
    dareas = bbox_area(dets)
    for i, (darea, det) in enumerate(zip(dareas, dets)):
        idet = insect_boxes(det, gts)
        iarea = bbox_area(idet)
        iods[i, :] = iarea / (darea + eps)
    return iods


def bbox_iou(dets, gts, eps=1e-12):
    ious = np.zeros(shape=(dets.shape[0], gts.shape[0]), dtype=np.float32)
    dareas = bbox_area(dets)
    gareas = bbox_area(gts)
    for i, (darea, det) in enumerate(zip(dareas, dets)):
        idet = insect_boxes(det, gts)
        iarea = bbox_area(idet)
        ious[i, :] = iarea / (darea + gareas - iarea + eps)
    return ious


def inv_normalize_box(bboxes, w, h):
    bboxes[:, 0] *= w
    bboxes[:, 1] *= h
    bboxes[:, 2] *= w
    bboxes[:, 3] *= h
    return bboxes


def xyxy2xywh(xyxy):
    x1, y1, x2, y2 = xyxy[..., 0:1], xyxy[..., 1:2], xyxy[..., 2:3], xyxy[..., 3:4]
    w, h = x2 - x1, y2 - y1
    return np.concatenate((x1, y1, w, h, xyxy[..., 4:]), axis=-1)


def xywh2xyxy(xywh):
    x1, y1, w, h = xywh[..., 0:1], xywh[..., 1:2], xywh[..., 2:3], xywh[..., 3:4]
    x2, y2 = x1 + w, y1 + h
    return np.concatenate((x1, y1, x2, y2, xywh[..., 4:]), axis=-1)