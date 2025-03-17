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
        
        
import pandas as pd

class CSVDeal:
    def __init__(self, csv_file):
        """
        构造函数，从给定的 CSV 文件中读取数据
        :param csv_file: CSV 文件的路径
        """
        self.df = pd.read_csv(csv_file)

    def merge_nonans(self, csv_files, key_column):
        for csv_file in csv_files:
            self.merge_nonan(csv_file, key_column)
    
    def merge_nonan(self, csv_file, key_column):
        """
        根据指定的键列合并另一个 CSV 文件的数据到当前 CSV 数据中
        :param csv_file: 另一个 CSV 文件的路径
        :param key_column: 用于匹配行的键列名
        """
        # 读取另一个 CSV 文件
        other_df = pd.read_csv(csv_file)

        # 合并两个 DataFrame
        merged_df = pd.merge(self.df, other_df, on=key_column, how='outer', suffixes=('_self', '_other'))

        # 遍历除键列之外的所有列
        for column in self.df.columns:
            if column != key_column:
                # 情况 1：两列值都非空且不相等
                condition1 = merged_df[f'{column}_self'].notnull() & merged_df[f'{column}_other'].notnull() & (
                        merged_df[f'{column}_self'] != merged_df[f'{column}_other'])
                if any(condition1):
                    # 打印警告信息
                    print(f"Warning: 在列 '{column}' 中，以下行的值不相等，将使用另一个 CSV 文件的值更新：")
                    print(merged_df[condition1][[key_column, f'{column}_self', f'{column}_other']])
                    # 使用另一个 CSV 文件的值更新当前 CSV
                    merged_df.loc[condition1, f'{column}_self'] = merged_df.loc[condition1, f'{column}_other']

                # 情况 2：当前 CSV 为空，另一个 CSV 非空
                condition2 = merged_df[f'{column}_self'].isnull() & merged_df[f'{column}_other'].notnull()
                merged_df.loc[condition2, f'{column}_self'] = merged_df.loc[condition2, f'{column}_other']

        # 重命名列并选择需要的列
        new_column_names = {f'{col}_self': col for col in self.df.columns}
        self.df = merged_df.rename(columns=new_column_names)[self.df.columns]

    def save(self, output_file):
        """
        将当前 DataFrame 保存到指定的 CSV 文件中
        :param output_file: 输出 CSV 文件的路径
        """
        self.df.to_csv(output_file, index=False)
