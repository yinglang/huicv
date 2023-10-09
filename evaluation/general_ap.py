import numpy as np


class ClassifierMatcher(object):
    def __call__(self, predict, gt):
        """
        Input:
            predict: shape=(..., num_examples, predict_dim); num_examples, for detection, it is detection result,
                for classification, it is number of data in dataset.
            gt:      shape=(..., num_gt, gt_dim)
        Output:
            has_matched: bool, shape=(..., num_examples)
            num_gt: shape=(..., )
        """
        assert predict.shape[-1] == 1 and gt.shape[-1] == 1 and predict.shape[-2] == gt.shape[-2]
        has_matched = gt[..., 0] == 1
        num_gt = has_matched.sum(axis=-1)
        return has_matched, num_gt


class GeneralAP(object):
    """
    1. match predict with gt: IOU(predict, gt)>th for detection, no operation for classification
    2. calculate tp and fp of each score threshold, tp => true positive => matched and positive (score > th)
       calculate recall and precision
    3. calculate ap
    """
    def __init__(self, matcher=ClassifierMatcher(), SAVE_RECALL_PRECISION_PATH=None):
        self.matcher = matcher
        self.SAVE_RECALL_PRECISION_PATH = SAVE_RECALL_PRECISION_PATH

    def __call__(self, predict, gt, score_idx=-1):
        """
        input:
            predict: shape=(..., num_examples, predict_dim); num_examples, for detection, it is detection result,
                for classification, it is number of data in dataset.
            gt:      shape=(..., num_gt, gt_dim)
            score_idx: int, predict[..., scores_idx] is scores of each prediction

        middle result:
            has_matched: bool, shape=(..., num_examples)
        output:
            ap: shape=(..., )
        """
        has_matched, num_gt = self.matcher(predict, gt)
        predict_scores = predict[..., score_idx]           # (..., num_examples)
        recall, precision, score_th = self.calculate_recall_precision(has_matched, predict_scores, num_gt)  # (..., num_examples)
        print(recall, precision)
        return self.cal_AP_of_recall(recall, precision)

    def calculate_recall_precision(self, has_matched, predict_scores, num_gt):
        idx = np.argsort(-predict_scores, axis=-1)
        has_matched, predict_scores = has_matched[idx], predict_scores[idx]  # (..., num_examples)

        TP = np.cumsum(has_matched.astype(np.float32), axis=-1)  # (..., num_examples)
        recall = TP / (num_gt + 1e-12)
        precision = TP / np.arange(1, len(TP) + 1)

        # (..., num_examples)
        recall, precision, chosen_idx = self._chosen_max_precision_for_each_recall(recall, precision)

        if len(recall) == 0:  # no det
            if num_gt == 0:  # no gt
                recall, precision = np.array([1.]), np.array([1.])
            else:  # have gt
                recall, precision = np.array([0]), np.array([0.])

        if self.SAVE_RECALL_PRECISION_PATH is not None:
            np.savez(self.SAVE_RECALL_PRECISION_PATH, recall=recall, precision=precision,
                     dets_score=predict_scores[chosen_idx])
        return recall, precision, predict_scores[chosen_idx]

    def _chosen_max_precision_for_each_recall(self, recall, precision):
        """
            for same recall (abs < 1e-10), may have multiple precision, chosen the best one as precision
        """
        last_r = -1
        final_recall = []
        final_precison = []
        chosen_idx = []
        for i, (r, p) in enumerate(zip(recall, precision)):
            # for each recall choose the max precision
            if abs(last_r - r) < 1e-10:
                continue
            final_recall.append(r)
            final_precison.append(p)
            last_r = r
            chosen_idx.append(i)
        recall = np.array(final_recall)
        precision = np.array(final_precison)
        return recall, precision, chosen_idx

    @staticmethod
    def cal_AP_of_recall(recall, precision, num_points=None, DEBUG=False):
        assert len(recall) == len(precision), ""
        if num_points is None:
            recall_th = np.linspace(.0, 1.00, int(np.round((1.00 - .0) / .01) + 1), endpoint=True)
        elif isinstance(num_points, int):
            recall_th = np.linspace(.0, 1.00, np.round((1.00 - .0) * (num_points-1)) + 1, endpoint=True)
        inds = np.searchsorted(recall, recall_th, side='left')
        choose_precisions = [precision[pi] if pi < len(recall) else 0 for pi in inds]
        if DEBUG:
            print("choose_precisions", choose_precisions)
        return np.sum(choose_precisions) / len(recall_th)


if __name__ == "__main__":
    AP = GeneralAP()
    predict = np.array([0.5, 0.6, 0.7, 0.8, 0.9, 1.0])[..., None]
    gt = np.array([1, 0, 0, 1, 1, 0])[..., None]
    print(AP(predict, gt))
