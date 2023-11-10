import os
import shutil
import sys
import argparse


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("dirs", type=str, nargs='+', default=[], help='keeped epochs')
    parser.add_argument("-ke", "--keep-epochs", type=int, nargs='+', default=[], help='keeped epochs')
    parser.add_argument("-dl", "--delete-last", action='store_true', default=False, help='delete last epoch')
    args = parser.parse_args()

    dirs = args.dirs
    keep_epochs = args.keep_epochs
    del_last = args.delete_last
    print(dirs, keep_epochs, del_last)

    s, e = len('epoch_'), -len('.pth')
    while len(dirs) != 0:
        the_dir = dirs.pop(0)
        epoch_fpath_map = {}
        for f in os.listdir(the_dir):
            fpath = os.path.join(the_dir, f)
            if os.path.isdir(fpath):
                dirs.append(fpath)
            else:
                if f.endswith('.pth') and not f.endswith('latest.pth'):
                    try:
                        epoch = int(f[s:e])
                        epoch_fpath_map[epoch] = fpath
                    except ValueError as exception:
                        print(exception, file=sys.stderr)
        if len(epoch_fpath_map) > 0:
            epochs = list(epoch_fpath_map.keys())
            keep_epoch = [] if del_last else [max(epochs)]
            keep_epoch += keep_epochs
            for epoch, fpath in epoch_fpath_map.items():
                if epoch not in keep_epoch:
                    print('rm {}'.format(fpath))
                    os.remove(fpath)
