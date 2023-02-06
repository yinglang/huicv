import copy
import os

import imageio
import numpy as np
import cv2
from pygifsicle import optimize  # pip install pygifsicle


def read_gif(gif_path):
    return [img for img in imageio.get_reader(gif_path)]


def merge_frame(w, h, nw, nh, sep, imgs):
    frame = np.zeros(((h + sep) * nh - sep, (w + sep) * nw - sep, imgs[0].shape[2]), dtype=np.uint8)
    for i, img in enumerate(imgs):
        ih, iw = i // nw, i % nw
        # np.array(img.resize((w, h)))
        img = cv2.resize(img, dsize=(w, h))
        frame[(h+sep)*ih: (h+sep)*ih+h, (w+sep)*iw: (w+sep)*iw+w] = img
    return frame


def imgs_to_gif(imgs, save_path, fps=20):
    with imageio.get_writer(save_path, 'GIF', mode='I', fps=fps) as writer:
        for img in imgs:
            writer.append_data(img)
    optimize(save_path)


def cut_edge(img, edge_colors=[(255, 255, 255), (0, 0, 0)], err=6):
    """
    :param img: shape=(h, w, 3/4)
    :return:
    """
    edge_colors = np.array(edge_colors)

    def is_edge(xs):
        if len(xs.shape) == 2:
            xs0 = xs[0, :3]
        elif len(xs.shape) == 1:
            xs0 = xs[0]
        else:
            raise ValueError
        is_edge_color = np.any(np.abs(xs0 - edge_colors).sum(axis=-1) <= err)
        return is_edge_color and np.all(xs[0] == xs)

    h, w = img.shape[:2]
    assert img.dtype == np.uint8, img.dtype

    l = 0
    for l in range(w):
        if not is_edge(img[:, l]):
            break

    r = w - 1
    for r in range(w-1, -1, -1):
        if not is_edge(img[:, r]):
            break

    t = 0
    for t in range(h):
        if not is_edge(img[t, :]):
            break

    b = h - 1
    for b in range(h-1, -1, -1):
        if not is_edge(img[b, :]):
            break
    assert t < b and l < r, f"{(l, t, r, b)}"
    return l, t, r, b


def cut_edge_for_gif(gif_imgs):
    l, t, r, b = cut_edge(gif_imgs[0])
    gif_imgs = [img[t:b, l:r]for img in gif_imgs]
    return gif_imgs


def resize_gif(gif_imgs, sf):
    imgs = []
    for img in gif_imgs:
        h, w = img.shape[:2]
        img = cv2.resize(img, dsize=(int(w*sf), int(h*sf)))
        imgs.append(img)
    return imgs


def black_img(template):
    template = copy.deepcopy(template)
    template[:] = 0
    return template


def create_gif(image_list, gif_name, duration=0.35):
    frames = []
    for image_name in image_list:
        frames.append(imageio.imread(image_name))
    frames.append(black_img(frames[-1]))
    imageio.mimsave(gif_name, frames, 'GIF', duration=duration)


def merge_imgs(imgs, sep=10):
    pass


def merge_gif(gif_names, saved_gif_names, nw, nh, sep=10, duration=0.35, dir_prefix=""):
    gifs = [read_gif(os.path.join(dir_prefix, gif_name)) for gif_name in gif_names]
    frames = []
    for imgs in zip(*gifs):
        h, w = imgs[0].shape[:2]
        img = merge_frame(w, h, nw, nh, sep, imgs=imgs)
        frames.append(img)
    imageio.mimsave(os.path.join(dir_prefix, saved_gif_names), frames, 'GIF', duration=duration)


if __name__ == '__main__':
    for gif_path in os.listdir('vis_result'):
        if gif_path.endswith('.gif'):
            gif_path = os.path.join('vis_result', gif_path)
            gif_imgs = read_gif(gif_path)
            gif_imgs = cut_edge_for_gif(gif_imgs)
            gif_imgs = resize_gif(gif_imgs, 0.75)
            imgs_to_gif(gif_imgs, gif_path, fps=2)
            optimize(gif_path)
