import numpy as np
import matplotlib.pyplot as plt


def show_density_as_scatter(X, Y, show=True, **kwargs):
    # 散点图，只能画出来点，但是重叠严重的地方看不出密度，对密度的可视化效果很差
    plt.scatter(X, Y, **kwargs)
    if show:
        plt.show()


def show_density_as_heatmap(X, Y, bins=None, show=True):  # recomand
    # 使用numpy的histogram2d函数统计点在二维区间内的数量
    H, xedges, yedges = np.histogram2d(X, Y, bins=bins)

    # 创建图像
    plt.imshow(H, interpolation='nearest', origin='lower', extent=[xedges[0], xedges[-1], yedges[0], yedges[-1]])
    plt.colorbar()
    if show:
        plt.show()


def show_meanY_and_density_of_Xbins(X, Y, bins=20, scale_count=True, label='', color='b', show=True):
    """
    1. split (x, y) into bins acorrding x
    2. plot(mean_x, mean_y) for each bins,
    3. plot(mean_x, num_points_of_each_bins) for each bins, show the distribution density of X
    4. for better view, we scale the count (num_points_of_each_bins) close to mean_y
    :param X:
    :param Y:
    :param bins:
    :param scale_count:
    :param label:
    :param color:
    :param show:
    :return:
    """
    idx = np.argsort(X)
    X, Y = X[idx], Y[idx]
    step = (X[-1] - X[0]) / bins
    start = X[0]
    mid_idx = [0]
    for i, x in enumerate(X):
        if x >= start + step:
            start += step
            mid_idx.append(i)
    mid_idx.append(len(X))

    mean_Y, mean_X, ele_count_per_bin = [], [], []
    for i in range(len(mid_idx) - 1):
        mean_Y.append(Y[mid_idx[i]:mid_idx[i + 1]].mean())
        mean_X.append(X[mid_idx[i]:mid_idx[i + 1]].mean())
        ele_count_per_bin.append(mid_idx[i + 1] - mid_idx[i])
    ele_count_per_bin = np.array(ele_count_per_bin) / len(X)

    # scale for better vis
    if scale_count:
        ele_count_per_bin = (ele_count_per_bin - min(ele_count_per_bin)) / (
                    max(ele_count_per_bin) - min(ele_count_per_bin))
        ele_count_per_bin = ele_count_per_bin * (max(mean_Y) - min(mean_Y)) + min(mean_Y)

    plt.plot(mean_X, mean_Y, color=color, label=f'{label}: mean X-Y')
    plt.scatter(mean_X, mean_Y, c=color)
    plt.plot(mean_X, ele_count_per_bin, '--', color=color, label=f'{label}: X-count')
    if show:
        plt.legend()
        plt.show()
    return mid_idx, mean_X, mean_Y
