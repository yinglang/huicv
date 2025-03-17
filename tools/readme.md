# Dist Utils

```py
import huicv.tools.dist_utils as dist_utils

if __name__ == '__main__':
    dist_utils.print_dist_args()
    dist_utils.setup()
    device = dist_utils.device()

    dataset = dist_utils.dataset(dataset)
    model = dist_utils.model(model)
    
    res_dict = {}
    for i, data in enumerate(dataset):
        res = model(transform(data))
        res_dict[data['idx']] = res["result"]
        if len(res_dict) >= 100:
            idxs = list(res_dict.keys())
            json.dump(res_dict, open(os.path.join(res_dir, f"{min(idxs)_max(idxs)}.json"), 'w'))
            res_dict = {}

    dist_utils.join(check_done_dir=os.path.join(res_dir, 'done'))
```

```shell
export WORLD_SIZE=2
export DIST_BACKEND="hui"

LOCAL_RANK=0 python example.py
LOCAL_RANK=1 python example.py
```

```shell
export WORLD_SIZE=2
export DIST_BACKEND="ddp"

LOCAL_RANK=0 python example.py
LOCAL_RANK=1 python example.py
```

# DirDict

A virtural dict, format as {id: result, ....}, save incremental data to disk
- 为了防止批量处理数据的时候出错的问题，我们需要按照一定的间隔定期保存结果，
- 每次保存完整的结果会花费很多时间，因此考虑只保存新增加的内容到磁盘，保存的结果放到一个目录下 =》incremental_update_and_save
- 为了读取方便，提供从一个目录读取所以结果文件的能力  =》 load_all

```py
from huicv.tools.common_utils import DirDict

json_dir = "results/"
dataset = [1, 2, 3, 4, 5]
def processing(data):
    return data * 2

dir_dict = DirDict(json_dir)
for i, data in enumerate(dataset):
    res = processing(data)
    dir_dict.incremental_update_and_save({i: res}, save_interval=100)
dir_dict.incremental_save()  # save left data

print(dir_dict.data_dict)
```

# CSVDeal

```py
from huicv.tools.common_utils import CSVDeal

csv_deal = CSVDeal("csv_file.csv")
csv_deal.merge_nonan("csv_file2.csv", key_column="idx")
csv_deal.save("csv_file_merge.csv")
```