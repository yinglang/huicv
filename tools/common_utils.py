import os,sys,json


class DirDict(object):
    """
        A virtural dict, format as {id: result, ....}, save incremental data to disk
        - 为了防止批量处理数据的时候出错的问题，我们需要按照一定的间隔定期保存结果，
        - 每次保存完整的结果会花费很多时间，因此考虑只保存新增加的内容到磁盘，保存的结果放到一个目录下 =》incremental_update_and_save
        - 为了读取方便，提供从一个目录读取所以结果文件的能力  =》 load_all
        Example:
            from huicv.tools.common_utils import DirDict
            dir_dict = DirDict(dict_dir)
            for i, data in enumerate(dataset):
                res = processing(data)
                dir_dict.incremental_update_and_save({i: res}, save_interval=100)
            dir_dict.incremental_save()  # save left data
            print(dir_dict.data_dict)
    """
    def __init__(self, dict_dir, id_type=int):
        self.id_type = id_type
        os.makedirs(dict_dir, exist_ok=True)
        self.data_dict = self.load_all(dict_dir)
        self.incremental_ids = []
        self.dict_dir = dict_dir

    def incremental_update(self, data):
        self.incremental_ids.extend(list(data.keys()))
        self.data_dict.update(data)
    
    def incremental_save(self):
        if len(self.incremental_ids) > 0:
            incremental_data_dict = {id: self.data_dict[id] for id in self.incremental_ids}
            ids = sorted(list(incremental_data_dict.keys()))
            json.dump(incremental_data_dict, open(os.path.join(self.dict_dir, f"{ids[0]}.json"), 'w'))
            self.incremental_ids = []

    def incremental_update_and_save(self, data, save_interval=100):
        self.incremental_update(data)
        if len(self.incremental_ids) >= save_interval:
            self.incremental_save()

    def load_all(self, load_dir):
        data_dict = {}
        if not os.path.exists(load_dir):
            return data_dict
        for filename in os.listdir(load_dir):
            if filename.endswith('.json'):
                data = json.load(open(os.path.join(load_dir, filename)))
                data = {self.id_type(id): d for id, d in data.items()}
            else:
                continue
            data_dict.update(data)
        return data_dict

    def save_all(self, save_path):
        json.dump(self.data_dict, open(save_path, 'w'))
