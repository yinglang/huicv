import numpy as np


def get_iou_match_results(coco_eval, cat_id, area_label=None):
    """
    coco_eval.evaluate是在调用evaluateImg对每个类别、尺度和图片计算匹配结果：
        self.evalImgs = [evaluateImg(imgId, catId, areaRng, maxDet)
                         for catId in catIds
                         for areaRng in p.areaRng
                         for imgId in p.imgIds
                     ]
        len(evalImgs) = len(cat) * len(areaRng) * len(imgs)
    
    Example:
    1. 匹配结果evalImgs中每个结果包含以下内容
        evalImgs[idx]:
            {
                # 评测的限定config
                'image_id': 1019,                                  # 评测结果是哪张图片的
                'category_id': 6,                                  # 评测结果是针对哪个类别
                'aRng': [0, 10000000000.0],                        # 评测结果是针对哪个尺度范围的
                'maxDet': 100,                                     # 评测结果使用的maxDet
    
                # 参与评测的input: det和gt，以及其对应的得分和是否为ignore
                'dtIds': [447304, 447305, 447509],                 
                'gtIds': [9950, 9951],
                'dtScores': [0.49818703532218933, 0.4331130385398865, 0.02021235227584839],
                'gtIgnore': array([0, 0]),
    
                # 不同IoU阈值匹配的结果, p.iouThrs = [0.5 , 0.55, 0.6 , 0.65, 0.7 , 0.75, 0.8 , 0.85, 0.9 , 0.95]
               'gtMatches': # (len(iouThrs), len(det)), 每个 gt 按IoU阈值匹配上的 det 的id, 0 表示没有匹配
                            array([[447305., 447304.],
                                   ...
                                   [447305., 447304.]]),
                'dtMatches': # dtm, (len(iouThrs), len(det)), 每个 det 按IoU阈值匹配上的 gt 的id, 0 表示没有匹配
                            array([[9951., 9950.,    0.],
                                   ...
                                   [9951., 9950.,    0.]]), 
                'dtIgnore': # dtIg, (len(iouThrs), len(det)), 每个 det 是否匹配上了一个ignore的gt
                            array([[False, False, False],
                                    ...
                                   [False, False, False]])
           }
    2. tp (True Positive) / fp (False positive) 的计算标准是:
        tps = np.logical_and(               dtm,  np.logical_not(dtIg) )
        fps = np.logical_and(np.logical_not(dtm), np.logical_not(dtIg) )
        也就是dtm有对应的匹配gt 且 该gt不是ignore 则为tp，反之则为fp
    """
    p = coco_eval.params
    N_c, N_a, N_i = len(p.catIds), len(p.areaRng), len(p.imgIds)
    
    print('[get_iou_match_results]: len(evalImgs) = len(cat) * len(areaRng) * len(imgs) :', len(coco_eval.evalImgs), '=', N_c * N_i * N_a)
    # match result of single image
    
    def get_evalImg_idx_range(cat_idx, area_idx):
        if area_idx is not None:
            return cat_idx * N_i * N_a + area_idx * N_i, cat_idx* N_i * N_a + (area_idx+1) * N_i
        else:
            return cat_idx * N_i * N_a, (cat_idx+1)* N_i * N_a
    
    cat_idx = p.catIds.index(cat_id)
    area_idx = p.areaRngLbl.index(area_label) if area_label is not None else None
    s, e = get_evalImg_idx_range(cat_idx, area_idx)
    cat_eval_img = coco_eval.evalImgs[s:e]
    return cat_eval_img


def accumulate_all_images_match_results(eval_imgs):
    gt_ids = np.concatenate([eval_img['gtIds'] for eval_img in eval_imgs], axis=-1)
    gt_ignore = np.concatenate([eval_img['gtIgnore'] for eval_img in eval_imgs], axis=-1)

    dt_ids = np.concatenate([eval_img['dtIds'] for eval_img in eval_imgs], axis=-1)
    dtm = np.concatenate([eval_img['dtMatches'] for eval_img in eval_imgs], axis=-1)
    dt_ignore = np.concatenate([eval_img['dtIgnore'] for eval_img in eval_imgs], axis=-1)
    dt_scors = np.concatenate([eval_img['dtScores'] for eval_img in eval_imgs], axis=-1)
    # different sorting method generates slightly different results.
    # mergesort is used to be consistent as Matlab implementation.
    inds = np.argsort(-dt_scors, kind='mergesort')
    sorted_dt_scors = dt_scors[inds]
    sorted_dtm = dtm[:, inds]
    sorted_dtm_ignore = dt_ignore[:, inds]
    sorted_dt_ids = dt_ids[inds]
    return {
        "dtIds": sorted_dt_ids,
        "dtScores": sorted_dt_scors,
        "dtMatches": sorted_dtm,
        "dtIgnore": sorted_dtm_ignore,

        "gtIds": gt_ids,
        "gtIgnore": gt_ignore,
    }

def get_fp_and_miss_from_iou_match_results(accu_eval_imgs, iou_idx, score_th=0.3):
    """
        当按照IoU匹配完成后，每个检测结果都有了是否匹配上GT的标志（dtm），这个标志可以看作是二分类的标签，匹配上了为1类，反之为0类。
        此时将检测结果按照得分降序排列，有下面三种分类错误的情况：
        - (FP): 那些分数高但是标签确是0类的就是高分错检（FP），这些检测结果的id记录为fp_det_ids
        - (Miss): 类似分数低但是标签为1类的就是低分丢失(missing)，这些检测结果的id记录为low_score_miss_det_ids，
            而这些检测结果匹配上的GT的id则记录为low_score_miss_gt_ids
        - (Miss): 而对于那些完全没有被匹配上的GT，则记录为miss_gt_ids或者pure_miss_gt_ids
    Return:
        fp_det_ids: [det_id, det_id, ....], sorted by det_scores, high score first
        low_score_miss_gt_ids: [gt_id, gt_id, ...], sorted by matched det_scores, low score first
        pure_miss_gt_ids: [gt_id, gt_id, ...], no matched gt
    """
    def filter_by_ignore(accu_eval_imgs, iou_idx):
        dtm = accu_eval_imgs['dtMatches'][iou_idx]  # accu_eval_imgs['dtMatches'].shape=(num_iouThrs, num_det)
        dt_scores = accu_eval_imgs['dtScores']   # sorted, 降序 (num_det,)
        dt_ids = accu_eval_imgs['dtIds']  # accu_eval_imgs['dtIds'].shape=(num_det,)
        gt_ids = accu_eval_imgs['gtIds']  # accu_eval_imgs['gtIds'].shape=(num_gt, )

        dt_ignore = accu_eval_imgs['dtIgnore'][iou_idx]
        non_dt_ignore = np.logical_not(dt_ignore)
        dtm = dtm[non_dt_ignore]
        dt_scores = dt_scores[non_dt_ignore]
        dt_ids = dt_ids[non_dt_ignore]

        gt_ignore = accu_eval_imgs['gtIgnore']
        non_dt_ignore = np.logical_not(gt_ignore)
        gt_ids = gt_ids[non_dt_ignore]

        return dtm, dt_scores, dt_ids, gt_ids

    dtm, dt_scores, dt_ids, gt_ids = filter_by_ignore(accu_eval_imgs, iou_idx)
    
    if score_th is not None:
        # searchsorted只能处理升序排列的数组
        th_idx = np.searchsorted(-dt_scores, -score_th, side='left')
        dtm_pos, dtm_neg = dtm[:th_idx], dtm[th_idx:]
    else:
        dtm_pos, dtm_neg = dtm, dtm

    fp_idx = np.nonzero(dtm_pos < 1)[0]   # 0 < 1表示没有gt匹配上该det, 没有gt匹配的idx越小（得分越高）,越是FP(错检)
    fp_idx = sorted(fp_idx)               # 确保高分排前面
    fp_det_ids = dt_ids[fp_idx]           # det id with high score but wrong det

    miss_idx = np.nonzero(dtm_neg > 0)[0] # 0 < 1表示没有gt匹配上该det, 有gt匹配的idx越大（得分越低）,越是Miss(漏检)
    miss_idx = sorted(miss_idx, key=lambda x: -x)  # 确保低分排前面
    low_score_miss_det_ids = dt_ids[th_idx+miss_idx]       # low score leading to missing
    low_score_miss_gt_ids = dtm_neg[miss_idx]        # 
    # low_score_miss_gt_ids = low_score_miss_gt_ids[low_score_miss_gt_ids > 0]  # 

    gt_ids_set = {int(gt_id) for gt_id in gt_ids.tolist()}
    matched_gt_set = {int(matched_gt) for matched_gt in dtm.tolist()}
    pure_miss_gt_ids = np.array(list(gt_ids_set - matched_gt_set))
    
    print(f"[get_fp_and_miss_from_iou_match_results]: {len(dtm)}({len(dtm_pos)} + {len(dtm_neg)}) results, \n\t"
            f"{len(fp_det_ids)} fp in {len(dtm_pos)} postive, {(len(low_score_miss_gt_ids))} low score missing in {len(dtm_neg)} negative, "
            f"and {len(pure_miss_gt_ids)} pure missing gt.")
    return fp_det_ids, low_score_miss_det_ids, low_score_miss_gt_ids, pure_miss_gt_ids


from pycocotools.cocoeval import COCOeval


def find_fp_and_missing(coco_gt_dt_or_coco_eval, cat_id, area_label='all', iou_th=0.75, score_th=0.3, re_evaluate=True):
    """
        当按照IoU匹配完成后，每个检测结果都有了是否匹配上GT的标志（dtm），这个标志可以看作是二分类的标签，匹配上了为1类，反之为0类。
        此时将检测结果按照得分降序排列，有下面三种分类错误的情况：
        - (FP): 那些分数高但是标签确是0类的就是高分错检（FP），这些检测结果的id记录为fp_det_ids
        - (Miss): 类似分数低但是标签为1类的就是低分丢失(missing)，这些检测结果的id记录为low_score_miss_det_ids，
            而这些检测结果匹配上的GT的id则记录为low_score_miss_gt_ids
        - (Miss): 而对于那些完全没有被匹配上的GT，则记录为miss_gt_ids或者pure_miss_gt_ids

    Example:
        coco_gt = COCO(ann_file)
        coco_dt = coco_gt.loadRes(coco_det_results)
        coco_eval = COCOeval(coco_gt, coco_dt, iouType='bbox')
    """
    if isinstance(coco_gt_dt_or_coco_eval, COCOeval):
        coco_eval = coco_gt_dt_or_coco_eval
    else:
        coco_gt, coco_dt = coco_gt_dt_or_coco_eval
        # 创建COCOeval对象
        coco_eval = COCOeval(coco_gt, coco_dt, iouType='bbox')
    if len(coco_eval.evalImgs) == 0 or re_evaluate:
        # 根据IoU匹配确定每个图片的gt和检测结果的匹配结果
        coco_eval.evaluate()

    # 1. 获得对应的类别和area约束下的匹配结果
    eval_imgs = get_iou_match_results(coco_eval, cat_id, area_label)
    # 2. 将所有图片的结果合并起来，并按得分排好序
    accu_eval_imgs = accumulate_all_images_match_results(eval_imgs)

    # 3. 跟据匹配结果，计算所有图片中的FP和missing
    p = coco_eval.params
    iou_idx = np.searchsorted(p.iouThrs, iou_th)
    assert np.abs(p.iouThrs[iou_idx] - iou_th) < 1e-6, f"there are no {iou_th} in {p.iouThrs}"
    fp_det_ids, low_score_miss_det_ids, low_score_miss_gt_ids, miss_gt_ids = get_fp_and_miss_from_iou_match_results(accu_eval_imgs, iou_idx, score_th)

    return fp_det_ids, low_score_miss_det_ids, low_score_miss_gt_ids, miss_gt_ids

