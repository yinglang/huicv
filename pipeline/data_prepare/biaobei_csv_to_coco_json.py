"""
读取CSV文件并转换为MS COCO格式.
    csv的格式如下：
        1) 一张图片一个csv文件，
        2) 这个文件的每行记录一个标注框的信息，[x1, y1, w, h, category] 总共五个内容，
        3) (x1,y1)(w,h)分别是框的左上角点和框的宽和高, category就写类别名称
"""


import csv
import json
import os
from PIL import Image
from tqdm import tqdm
import argparse
from dataset_config import category_to_id
print(category_to_id)


def get_files_with_extensions(directory, extensions = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff']):
    # 支持的图片文件扩展名, extensions
    # 图片路径列表
    image_paths = []
    # 遍历目录
    for root, dirs, files in os.walk(directory):
        for file in files:
            # 检查文件扩展名是否是图片格式
            if any(file.lower().endswith(ext) for ext in extensions):
                # 获取相对路径并添加到列表中
                relative_path = os.path.relpath(os.path.join(root, file), directory)
                image_paths.append(relative_path)

    return image_paths


def get_seg_from_box(box):
    x1, y1, w, h = box
    x2, y2 = x1 + w, y1 + h
    return [[x1, y1], [x2, y1], [x2, y2], [x1, y2]]    


def convert_csv_to_coco(csv_dir, img_dir, refer_json_path, json_file_path):

    # 初始化一个空的COCO数据结构
    coco_data = {
        "images": [],
        "annotations": [],
        "categories": [{"id": id, "name": name, "supercategory": name} for name, id in category_to_id.items()]
    }

    if img_dir is not None:
        # get all pathes
        paths = get_files_with_extensions(img_dir)
        image_id = 1
        for img_path in tqdm(paths, desc="load image info"):
            # img_path = os.path.join(img_dir, img_path)

            # 添加图像信息
            img = Image.open(os.path.join(img_dir, img_path))
            image_data = {
                "id": image_id,
                "width": img.width,    # 假设w是图像的宽度
                "height": img.height,  # 假设h是图像的高度
                "file_name": img_path # 假设文件名遵循此格式
            }
            coco_data['images'].append(image_data)
            image_id += 1
    elif refer_json_path is not None:
        jd = json.load(open(refer_json_path))
        coco_data['images'] = jd['images']
    else:
        raise ValueError()


    annotation_id = 1
    for img_info in tqdm(coco_data['images'], desc='load annotations'):
        img_id, img_path = img_info['id'], img_info['file_name']
    
        # train/xxx.jpg => xxx.csv
        _, image_name = os.path.split(img_path)
        idx = image_name.rfind('.')
        assert idx > 0, f"get unexcepted file {img_path}"
        csv_name = image_name[:idx] + ".csv"

        csv_path = os.path.join(csv_dir, csv_name)
        # reading CSV
        with open(csv_path) as csvfile:
            reader = csv.reader(csvfile)
            # next(reader, None)  # 跳过标题行（如果有）
            for row in reader:
                # 解析CSV行数据
                x1, y1, w, h = map(float, row[:4])
                category_name = row[4]
                # 检查类别名称是否在映射中
                if category_name not in category_to_id:
                    raise ValueError(f"未知类别: {category_name}")

                # 添加标注信息
                bbox = [x1, y1, w, h]
                annotation_data = {
                    "id": annotation_id,
                    "image_id": img_id,
                    "category_id": category_to_id[category_name],
                    "segmentation": [get_seg_from_box(bbox)],
                    "area": w * h,
                    "bbox": bbox,
                    "iscrowd": 0
                }
                coco_data['annotations'].append(annotation_data)

                # 更新ID
                annotation_id += 1
        

    # 写入JSON文件
    os.makedirs(os.path.split(json_file_path)[0], exist_ok=True)
    with open(json_file_path, 'w') as jsonfile:
        json.dump(coco_data, jsonfile)
        print(f"dump {len(coco_data['annotations'])} annotations in {len(coco_data['images'])} images to {json_file_path}.")


if __name__ == '__main__':
    """
    将images字段中涉及到的图片对应的csv格式的标注转换成json格式 （annotations字段），
    对于images字段，如果给定一个图片的根目录（--img），将递归解析加载下面的所有图片获得长宽信息，生成image_id（图片不可重名）
      如果给定一个参考的json标注，将直接复制该文件中的images字段
    """
    # 创建解析器
    parser = argparse.ArgumentParser(description='Example of how to turn csv to coco json format.')

    # 添加三个字符类型的参数
    parser.add_argument('--csv', type=str, help='Directory of csv.')
    parser.add_argument('--img', type=str, default="", help='Root directory of image.')
    parser.add_argument('--save-json', type=str, help='Saved json path.')
    parser.add_argument('--refer-json', type=str, default="", help='json to obtain images.')

    # 解析命令行参数
    args = parser.parse_args()
    # 使用示例
    csv_dir = args.csv          # 'labels_plus/with_warningwords'  # CSV文件路径
    img_dir = None if len(args.img) == 0 else args.img          # 'images/'
    json_file_path = args.save_json  # 'annotations_plus/instances_all.json'  # 输出的JSON文件路径
    refer_json_path = None if len(args.refer_json) == 0 else args.refer_json
    assert (img_dir is None and refer_json_path is not None) or (img_dir is not None and refer_json_path is None), \
        "neither img_dir or refer_json_path can be given to provied images information." 
    convert_csv_to_coco(csv_dir, img_dir, refer_json_path, json_file_path)

