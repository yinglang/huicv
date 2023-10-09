import numpy as np
import matplotlib.pyplot as plt
from copy import deepcopy


def show_images(imgs, plot_func=None, mxn=None, fig_kwargs={}, titles=None, show=True):
    if mxn is None:
        m = int(np.round(np.sqrt(len(imgs))))
        n = int(np.ceil(len(imgs) / m))
        mxn = (m, n)
    num_rows, num_cols = mxn
    if 'figsize' not in fig_kwargs:
        fig_kwargs = deepcopy(fig_kwargs)
        W = max([sum([img.shape[1] for img in imgs[i*num_cols:(i+1)*num_cols]]) for i in range(num_rows)])
        H = max([sum([img.shape[0] for img in imgs[j::num_cols]]) for j in range(num_cols)])
        fig_kwargs['figsize'] = (int(W/100), int(H/100))  # dpi=100
    fig, axes = plt.subplots(num_rows, num_cols, **fig_kwargs)  # figsize=(4, 3)
    for i in range(num_rows):
        for j in range(num_cols):
            idx = i * num_cols + j
            # 获取当前子图的坐标轴
            if not hasattr(axes, 'shape'):
                ax = axes
            elif len(axes.shape) == 2:
                ax = axes[i, j]
            elif len(axes.shape) == 1:  # num_rows = 1 or num_cols = 1
                ax = axes[idx]
            else:
                raise ValueError

            if idx < len(imgs):
                ax.imshow(imgs[idx])
                if plot_func is not None:
                    plot_func(idx, ax)
                if titles is not None:
                    ax.set_title(titles[idx])
            else:
                plt.delaxes(ax)
    # 调整子图之间的间距
    plt.tight_layout()
    if show:
        plt.show()

