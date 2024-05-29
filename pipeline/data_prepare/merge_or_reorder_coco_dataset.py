import json
import warnings
import os 

def check_no_repeat_id(merge_json_data):
    assert len(set([img_info['id'] for img_info in merge_json_data['images']])) == len(merge_json_data['images'])
    assert len(set([ann_info['id'] for ann_info in merge_json_data['annotations']])) == len(merge_json_data['annotations'])

def offset_image_and_annotation_id(json_data, annotation_id_offset=0, image_id_offset=0):
    for img_info in json_data['images']:
        img_info['id'] += image_id_offset

    for ann in json_data['annotations']:
        ann['id'] += annotation_id_offset
        ann['image_id'] += image_id_offset
    return json_data

def merge_dataset(json_datas):
    merge_json_data = {"images": [], "annotations": [], "categories": None}
    annotation_id_offset, image_id_offset = 0, 0
    for json_data in json_datas:
        if isinstance(json_data, str):
            json_data = json.load(open(json_data))
        print(f"load dataset with {len(json_data['images'])} images, {len(json_data['annotations'])} annotations, {len(json_data['categories'])} categories.")
        if merge_json_data["categories"] is None:
            merge_json_data["categories"] = json_data["categories"]
        else:
            if merge_json_data["categories"] != json_data["categories"]:
                warnings.warn(f'categories mismatch {merge_json_data["categories"]} vs {json_data["categories"]}')
        
        json_data = offset_image_and_annotation_id(json_data, annotation_id_offset, image_id_offset)
        annotation_id_offset = max([ann['id'] for ann in json_data['annotations']]) + 1  # 以防id从0开始
        image_id_offset = max([img['id'] for img in json_data['images']]) + 1            # 以防id从0开始

        merge_json_data["images"].extend(json_data['images'])
        merge_json_data["annotations"].extend(json_data['annotations'])
    print(f"merged dataset with {len(merge_json_data['images'])} images, {len(merge_json_data['annotations'])} annotations, {len(merge_json_data['categories'])} categories.")
    
    check_no_repeat_id(merge_json_data)
    return merge_json_data

def reorder_dataset(json_data):
    if isinstance(json_data, str):
        json_data = json.load(open(json_data))
    
    img_ids = [img_info['id'] for img_info in json_data['images']]
    img_id_map = {img_id: new_img_id+1 for new_img_id, img_id in enumerate(sorted(img_ids))}

    ann_ids = [ann['id'] for ann in json_data['annotations']]
    ann_id_map = {ann_id: new_ann_id+1 for new_ann_id, ann_id in enumerate(sorted(ann_ids))}

    for img_info in json_data['images']:
        img_info['id'] = img_id_map[img_info['id']]
    for ann_info in json_data['annotations']:
        ann_info['id'] = ann_id_map[ann_info['id']]
        ann_info['image_id'] = img_id_map[ann_info['image_id']]

    check_no_repeat_id(json_data)
    return json_data

def merge_or_reorder_dataset(coco_json_files, save_json_path, reorder=True):
    json_data = merge_dataset(coco_json_files)
    if reorder:
        json_data = reorder_dataset(json_data)

    jd = json.load(open(coco_json_files[0]))
    jd['images'] = json_data['images']
    jd['annotations'] = json_data['annotations']
    jd["categories"] = json_data["categories"]

    os.makedirs(os.path.split(save_json_path)[0], exist_ok=True)
    with open(save_json_path, 'w') as outfile:
        json.dump(json_data, outfile)
        print(f"merged json save to：{save_json_path}")



if __name__ == '__main__':
    import argparse
    """
        先按照每个json文件中的最大id作为offset，对后一个json文件中的id进行调整，以完成merge
        merge结束后，如果reorder==True,则对merge后的json_data中的id重新编号，从1开始，连续编号
    """
    # 创建解析器
    parser = argparse.ArgumentParser(description='Example of how to split dataset in n pahse')

    # 添加三个字符类型的参数
    parser.add_argument('--coco-json-files', type=str, help='coco format json annotation files.')
    parser.add_argument('--save-json-path', type=str, help='save json file for merged version.')
    
    parser.add_argument('--reorder', type=str, default="True", help='Whether reorder image_id and annotation_id after merge.')

    # 解析命令行参数
    args = parser.parse_args()
    # 使用示例

    coco_json_files = [json_file.strip() for json_file in args.coco_json_files.split(",") if len(json_file.strip()) > 0]
    save_json_path = args.save_json_path
    reorder = eval(args.reorder)
    merge_or_reorder_dataset(coco_json_files, save_json_path, reorder)
