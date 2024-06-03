TITLE_FONTSIZE = 10
FIGSIZE = (12, 8)


def get_clear_fig(H, W):
    import matplotlib.pyplot as plt
    fig = plt.figure()
    dpi = fig.get_dpi()
    EPS = 1e-2
    fig.set_size_inches((W + EPS) / dpi, (H + EPS) / dpi)
    plt.subplots_adjust(left=0, right=1, bottom=0, top=1)
    ax = plt.gca()
    ax.axis('off')
    return fig, ax