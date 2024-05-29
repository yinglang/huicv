import random
from pycocotools.coco import COCO
import os
import json
import shutil
from tqdm import tqdm


def random_split_images(image_paths, ratios):
    """
    将图像路径列表按照给定比例随机分成若干份。
    
    :param image_paths: 图像路径的列表
    :param ratios: 分割比例的列表，比例之和必须为1
    :return: 分割后的图像路径列表
    """
    # 首先，确保所有比例加起来等于1
    assert sum(ratios) == 1, "所有比例之和必须等于1"
    
    # 打乱图像路径列表
    random.shuffle(image_paths)
    
    # 计算每个比例对应的图像数量
    split_indices = [0]
    cumulative_ratio = 0
    for ratio in ratios:
        cumulative_ratio += ratio
        split_indices.append(int(cumulative_ratio * len(image_paths)))
    split_indices[-1] = len(image_paths)
    
    # 根据计算出的索引分割列表
    split_lists = [image_paths[split_indices[i]:split_indices[i+1]] for i in range(len(ratios))]
    
    return split_lists


def phase_split_images(img2ann_count, num_phase=10, set_ratio=[0.9, 0.1]):
    """
        先按图片中的标注数量进行排序，然后进行分段，分成num_phase段
        对每段的中的图片按给定的比例set_ratio进行随机划分
    """
    img_ann_count = sorted(img2ann_count.items(), key=lambda pair: -pair[-1])
    num_img = len(img_ann_count)
    if num_phase > 1:
        num_img_per_phase = num_img // (num_phase - 1)

    split_data = [[] for _ in set_ratio]
    for i in range(num_phase):
        img_ann_count_phase = img_ann_count[i*num_img_per_phase: (i +1)* num_img_per_phase]
        splited_img_phase = random_split_images(img_ann_count_phase, set_ratio)
        for set_i, i_th_splited_img_phase in enumerate(splited_img_phase):
            split_data[set_i].extend(i_th_splited_img_phase)
    return split_data

def get_subset_json_for_given_image(coco, given_image_ids):
    if isinstance(coco, str):
        coco = COCO(coco)

    images_to_keep = coco.loadImgs(given_image_ids)

    annotations_to_keep = []
    for image_info in images_to_keep:
        ann_ids = coco.getAnnIds(imgIds=image_info['id'])
        anns = coco.loadAnns(ann_ids)
        annotations_to_keep.extend(anns)

    new_dataset = {key: coco.dataset[key] for key in coco.dataset if key not in ["images", "annotations"]}
    new_dataset.update({
        "images": images_to_keep, 
        "annotations": annotations_to_keep
    })
    return new_dataset


def create_subset_images_dir(coco, given_image_ids, src_image_root, target_directory, mode='move'):
    # 确保目标目录存在
    if not os.path.exists(target_directory):
        os.makedirs(target_directory)
    if mode == 'copy':
        func = shutil.copy
    elif mode == 'move':
        func = shutil.move

    print(f"copy image from {src_image_root} to {target_directory}")
    # 对于给定的每个image_id，移动对应的图片
    for image_id in tqdm(given_image_ids):
        # 获取图片信息
        image_info = coco.loadImgs(image_id)[0]
        # 获取图片的文件名
        file_name = image_info['file_name']
        original_image_path = os.path.join(src_image_root, file_name)
        target_image_path = os.path.join(target_directory, file_name)
        
        # 检查图片是否存在
        if os.path.exists(original_image_path):
            # 移动图片
            func(original_image_path, target_image_path)
        else:
            print(f"Image {original_image_path} does't exists")


def split_and_save_dataset(
    all_ann_file, save_prefix, datasets_name = ["train", "val"],
    set_ratio=[0.9, 0.1], num_phase=10, 
    image_root=None, save_image_root=None, save_image_mode='move'
    ):
    coco = COCO(all_ann_file)
    img2ann_count = {img_id: len(anns) for img_id, anns in coco.imgToAnns.items()}

    datasets = phase_split_images(img2ann_count, num_phase=num_phase, set_ratio=set_ratio)
    
    
    datasets_img = [[img_data[0] for img_data in dataset] for dataset in datasets]
    datasets_ann_count = [[img_data[1] for img_data in dataset] for dataset in datasets]
    
    num_imgs = sum([len(dataset_img) for name, dataset_img in zip(datasets_name, datasets_img)])
    num_anns = sum([sum(dataset_ann_count) for name, dataset_ann_count in zip(datasets_name, datasets_ann_count)])
    print("Image count of splited dataset:", *[f"{name}: {len(dataset_img)}({len(dataset_img) / num_imgs:.3})" for name, dataset_img in zip(datasets_name, datasets_img)])
    print("Image count of splited dataset:", *[f"{name}: {sum(dataset_ann_count)}({sum(dataset_ann_count) / num_anns:.3})" for name, dataset_ann_count in zip(datasets_name, datasets_ann_count)])
    for name, dataset_img in zip(datasets_name, datasets_img):
        json_data = get_subset_json_for_given_image(coco, dataset_img)

        subset_json_path = f"{save_prefix}{name}.json"
        with open(subset_json_path, 'w') as outfile:
            json.dump(json_data, outfile)
        print(f"subset ({name}) json save to：{subset_json_path}")

    if save_image_root is not None and image_root is not None:
        for name, dataset_img in zip(datasets_name, datasets_img):
            create_subset_images_dir(coco, dataset_img, image_root, os.path.join(save_image_root, name), save_image_mode)


if __name__ == '__main__':
    import argparse
    """
        先按图片中的标注数量进行排序，然后进行分段，分成num_phase段
        对每段的中的图片按给定的比例set_ratio进行随机划分
        保证划分后的数据集中的标注数量也是符合比例的，并且标注多的少的图片在训练集和测试集中都有
    """
    # 创建解析器
    parser = argparse.ArgumentParser(description='Example of how to split dataset in n pahse')

    # 添加三个字符类型的参数
    parser.add_argument('--all-ann-file', type=str, help='coco format json annotation file.')
    parser.add_argument('--save-prefix', type=str, help='save dir of json file for splited sub set.')
    
    parser.add_argument('--set-ratio', type=str, default="[0.9,0.1]", help='ratio of each subset.')
    parser.add_argument('--datasets-name', type=str, default='["train", "val"]', help='name of subset.')
    parser.add_argument('--num-phase', type=int, default=10, help='number of phase to split subset.')

    parser.add_argument('--image-root', type=str, default='', help='image root dir of existing dataset.')
    parser.add_argument('--save-image-root', type=str, default='', help='image root dir for save sub dataset.')
    parser.add_argument('--save-image-mode', type=str, default='move', help='copy or move')

    # 解析命令行参数
    args = parser.parse_args()
    # 使用示例
    save_prefix = args.save_prefix
    datasets_name=eval(args.datasets_name)
    split_ratio = eval(args.set_ratio)
    image_root = None if len(args.image_root) == 0 else args.image_root
    save_image_root = None if len(args.save_image_root) == 0 else args.save_image_root

    split_and_save_dataset(
        args.all_ann_file, save_prefix, datasets_name, split_ratio, args.num_phase,
        image_root, save_image_root, args.save_image_mode
    )
