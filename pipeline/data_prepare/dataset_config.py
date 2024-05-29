# 定义MS COCO的类别名称到ID的映射，这里需要根据实际情况进行修改
category_to_id = {
    'logo': 1,
    'banner': 2,
    'warningwords': 3,
    'copywriting': 4,
    'region': 5,
    'subimage': 6,
    'gaussianblur': 7,
    'commodity': 8,
    'warningwords_region': 9
}

id2name = {id: cat for cat, id in category_to_id.items()}
