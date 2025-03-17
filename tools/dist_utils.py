import torch.distributed as dist
import torch
from torch.nn.parallel import DistributedDataParallel as DDP
import os, shutil
import time

torch_dist_activate = False
mp_backend = 'ddp'  # 'hui'

class TorchDist:

    @staticmethod
    def setup():
        global torch_dist_activate
        torch.distributed.init_process_group(backend='nccl')
        torch.cuda.set_device(int((os.environ['LOCAL_RANK']))) #int(os.getenv('LOCAL_RANK', 0)))
        torch_dist_activate = True

    @staticmethod
    def join(check_done_dir=None):
        if torch_dist_activate:
            dist.barrier()  # wait for all processes to finish
            if torch.distributed.get_rank() == 0:
                print("finished")
            time.sleep(30)
            dist.destroy_process_group()

    @staticmethod
    def get_rank():
        if torch_dist_activate:
            return dist.get_rank()
        else:
            return 0
    @staticmethod
    def get_world_size():
        if torch_dist_activate:
            return dist.get_world_size()
        else:
            return 1
    @staticmethod
    def wait():
        if torch_dist_activate:
            dist.barrier()
    @staticmethod
    def model(_model):
        if torch_dist_activate:
            return DDP(_model, device_ids=[int(os.environ['LOCAL_RANK'])])
        else:
            return _model
    
    @staticmethod
    def dataset(_dataset):
        raise NotImplementedError

    @staticmethod
    def device():
        return dist.get_rank() if torch_dist_activate else 0


class HuiDist:
    world_size = None
    local_rank = None
    cuda_visible_devices = None
    # rank = None

    @staticmethod
    def setup():
        HuiDist.world_size = int(os.environ['WORLD_SIZE'])
        if 'LOCAL_RANK' in os.environ and os.environ['LOCAL_RANK'] != '':
            HuiDist.local_rank = int(os.environ['LOCAL_RANK'])
        else:
            HuiDist.local_rank = int(os.environ['HUI_LOCAL_RANK'])  # to avoid xtuner problem
        gpus = [int(i) for i in range(len(os.getenv('CUDA_VISIBLE_DEVICES', "0").split(",")))]
        HuiDist.cuda_visible_devices = gpus

    @staticmethod
    def join(check_done_dir='/tmp/check_done'):
        os.makedirs(check_done_dir, exist_ok=True)
        # create a file to indicate that the current gpu has finished
        with open(os.path.join(check_done_dir, f'gpu{HuiDist.get_rank()}'), 'w') as f:
            pass
        
        check_i = 0
        done_file = os.listdir(check_done_dir)
        while len(done_file) < HuiDist.get_world_size(): # check if all gpu has finished
            check_i += 1
            if check_i % 10 == 0 and HuiDist.get_rank() == 0:
                print(f"GPU {HuiDist.get_rank()}: {done_file} has done, wait for other gpu to finish")
                
            time.sleep(30)
            done_file = os.listdir(check_done_dir)
        # if HuiDist.get_rank() == 0: # delete will broke before check for other process
        #     try:
        #         shutil.rmtree(check_done_dir)
        #     except FileNotFoundError:
        #         pass

    @staticmethod
    def get_rank():
        return HuiDist.local_rank

    @staticmethod
    def get_world_size():
        return HuiDist.world_size

    @staticmethod
    def wait():
        pass

    @staticmethod
    def device():
        if len(HuiDist.cuda_visible_devices) == HuiDist.world_size:
            return HuiDist.cuda_visible_devices[HuiDist.local_rank]
        else:
            assert len(HuiDist.cuda_visible_devices) == 1, "cuda_visible_devices length must be 1 or equal to world_size"
            return 0

    @staticmethod
    def model(_model):
        return _model
    
    @staticmethod
    def dataset(_dataset):
        dist_utils = HuiDist
        d_n = dist_utils.get_world_size()
        d_i = dist_utils.get_rank()
        if isinstance(_dataset, list):
            dataset = dataset[d_i::d_n]
        else:
            raise NotImplementedError
        return dataset


def set_func_for_mp_backend(backend='ddp'):
    global mp_backend, join, get_rank, get_world_size, wait, model, device, dataset
    mp_backend = backend
    if backend == 'ddp':
        # setup = TorchDist.setup
        join = TorchDist.join
        get_rank = TorchDist.get_rank
        get_world_size = TorchDist.get_world_size
        wait = TorchDist.wait
        model = TorchDist.model
        device = TorchDist.device
        dataset = TorchDist.dataset
    elif backend == 'hui':
        # setup = HuiDist.setup
        join = HuiDist.join
        get_rank = HuiDist.get_rank
        get_world_size = HuiDist.get_world_size
        wait = HuiDist.wait
        model = HuiDist.model
        device = HuiDist.device
        dataset = HuiDist.dataset
    else:
        raise VauleError(f'backend {backend} not supported')


def setup(backend='ddp'):
    if backend is None:
        backend = os.environ['DIST_BACKEND']
    set_func_for_mp_backend(backend)
    if backend == 'ddp':
        TorchDist.setup()
    elif backend == 'hui':
        HuiDist.setup()
    else:
        raise VauleError(f'backend {backend} not supported')


def print_dist_args():
    print("dist args:")
    for key in ["WORLD_SIZE", "LOCAL_RANK", "HUI_LOCAL_RANK", "DIST_BACKEND"]:
        print('\t', key, os.environ.get(key, ""))


join = TorchDist.join
get_rank = TorchDist.get_rank
get_world_size = TorchDist.get_world_size
wait = TorchDist.wait
model = TorchDist.model
device = TorchDist.device
dataset = TorchDist.dataset


# def main_run(_model, _dataset, infer_func):
#     if __name__ == '__main__':
#         print_dist_args()
#         setup()
#         _device = device()
        
#         _dataset = dataset(_dataset)
#         _model = model(_model)
        
        
#         infer_func(_model, _dataset, _device)
        
#         dist_utils.join(check_done_dir=os.path.join(res_dir, 'done'))