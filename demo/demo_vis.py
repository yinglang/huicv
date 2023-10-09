# from huicv.visualization import show_images
# import numpy as np
#
# images = [np.random.rand(200, 300, 3) for _ in range(3)]
#
# # show multiple images
# show_images(images)
#
# # set layout with mxn and titles
# show_images(images, mxn=(1, 3), titles=['figure1', 'figure2', 'figure3'])
#
#
# def plot_func(idx, ax):
#     ax.set_title(f"figure {idx}")
#
#
# # define yours plot func
# show_images(images, plot_func=plot_func)


import numpy as np
import matplotlib.pyplot as plt
from huicv.visualization.analysis import show_density_as_heatmap, show_meanY_and_density_of_Xbins
data_a, data_b = np.random.randn(2, 10000)

# 散点图，只能画出来点，但是重叠严重的地方看不出密度，对密度的可视化效果很差
plt.scatter(data_a, data_b)
plt.show()
# show distribution density of (a, b) \in (data_a, data_b)
show_density_as_heatmap(data_a, data_b, (50, 50))
# bins X, 用于查看X,Y是否相关
show_meanY_and_density_of_Xbins(data_a, data_b)