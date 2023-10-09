from huicv.coco_utils.coco_ann_utils import dump_coco_annotation
import os, json


if __name__ == "__main__":
    from argparse import ArgumentParser
    parser = ArgumentParser()
    parser.add_argument('ann')
    parser.add_argument('--save-ann', default='')
    parser.add_argument('--round', default=3)
    args = parser.parse_args()

    if os.path.isfile(args.ann):
        save_ann = args.save_ann if len(args.save_ann) > 0 else args.ann
        os.makedirs(os.path.split(save_ann)[0], exist_ok=True)
        jd = json.load(open(args.ann))
        dump_coco_annotation(jd, save_ann, n_round=args.round)
        print('save ann to', save_ann)
    elif os.path.isdir(args.ann):
        assert len(args.save_ann) == 0, '--save-ann can not be specified while ann is dir.'
        for root, dirs, files in os.walk(args.ann):
            for file in files:
                if file.endswith('.json'):
                    ann_path = os.path.join(root, file)
                    jd = json.load(open(ann_path))
                    dump_coco_annotation(jd, ann_path, n_round=args.round)
                    print('save ann to', ann_path)
    else:
        raise ValueError(f"{args.ann} is neither dir nor file.")

