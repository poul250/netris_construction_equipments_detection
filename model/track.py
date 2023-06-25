import numpy as np
import cv2
from collections import deque
from scipy.spatial import distance_matrix

"""
X - object features
y - object ids
"""
def match_ids_single(X_prev, X, y_prev, dist_thres):
    if len(X_prev) == 0:
        assert(len(y_prev) == 0)
        y = -np.ones(X.shape[0], dtype=int)
        return y
    if len(X) == 0:
        y = np.array([], dtype=int)
        return y
    assert(y_prev.shape[0] == X_prev.shape[0])
    # y = np.zeros(X.shape[0], dtype=int)
    dist_matr = distance_matrix(X_prev, X)
    # print(dist_matr)
    mins_args = np.argmin(dist_matr, axis=0) # closest object X_pre[j] to object X[i] for all i
    mins = dist_matr[mins_args, np.arange(dist_matr.shape[1])]
    # print(mins_args, mins)
    a = (mins >= dist_thres)
    a_n = np.count_nonzero(a)
    mins_args[a] = -1
    # mins_args[a] = np.arange(max_id + 1, max_id + a_n + 1)
    # max_id += a_n

    # checking duplicate ids in mins_args=y, and leave only the one with min distance (the rest will be new ids)
    # ids here are indexes in y_prev array though, they will be mapped to values from y_prev at the end
    ids, ids_count = np.unique(mins_args, return_counts=True)
    mins_args_old = np.copy(mins_args)
    for id, cnt in zip(ids, ids_count):
        if id < 0 or cnt == 1:
            continue
        id_pos = np.where(mins_args_old == id)[0]
        chosen_pos = id_pos[np.argmin(mins[id_pos])]
        mins_args[id_pos] = -1
        mins_args[chosen_pos] = id
    y_prev_extend = np.concatenate((y_prev, np.array([-1])))
    y = y_prev_extend[mins_args]
    return y

"""
set negative elements in y to max_id+1, max_id+2, ... max_id+n and return max_id := max_id + n
"""
def make_new_ids(y, max_id):
    y_fix = np.copy(y)
    a = (y < 0)
    a_n = np.count_nonzero(a)
    y_fix[a] = np.arange(max_id + 1, max_id + a_n + 1)
    return y_fix, max_id + a_n

def match_ids_multi(X_prevs, X, y_prevs, dist_thres):
    if len(X) == 0:
        y = np.array([], dtype=int)
        return y
    ys = np.zeros((len(X_prevs), X.shape[0]), dtype=int)
    for i, (X_prev, y_prev) in enumerate(zip(X_prevs, y_prevs)):
        # print("in match_ids_multi: calling single:", X_prev.shape, X.shape, y_prev.shape)
        y = match_ids_single(X_prev, X, y_prev, dist_thres)
        ys[i] = y
    y = vote_in_columns(ys)
    return y

def vote_in_columns(ys):
    y = np.zeros_like(ys[0])
    forbidden_ids = set()
    for j in range(ys.shape[1]):
        for fid in forbidden_ids:
            ys[:, j][ys[:, j] == fid] = -1
        ids, ids_count = np.unique(ys[:, j][ys[:, j] >= 0], return_counts=True)
        if len(ids_count) == 0:
            id_win = -1
        else:
            id_win = ids[np.argmax(ids_count)]
        y[j] = id_win
        forbidden_ids.add(id_win)
    return y

def img_embedding(img, n_h, n_w):
    # print("img_embedding", img.shape, n_w, n_h)
    img_ft = cv2.resize(img, (n_w, n_h), interpolation=cv2.INTER_AREA)
    assert(img_ft.shape[0] == n_w)
    assert(img_ft.shape[1] == n_h)
    return img_ft

def crop_box(img, box):
    x1, y1, x2, y2 = box
    return img[y1:y2, x1:x2]

"""
X.shape = (N, 4): features are x1,y1,x2,y2
"""
def box_features(X):
    box_c = (X[:, 0:2] + X[:, 2:4]) / 2. # center
    box_s = X[:, 2:4] - X[:, 0:2] # radius
    X_out = np.hstack([box_c, box_s])
    return X_out

def make_all_features(box, clas, img):
    n_classes = 4 # TODO ? just a normalization factor
    # if img is not None:
        # img_crop = crop_box(img, box[0])
        # h, w, channels = img.shape
    img_crop = crop_box(img, box[0])
    h, w, channels = img.shape

    coef_box = 15.0
    coef_clas = 50.0
    coef_embed = 1.0
    div_embed = 256. if np.issubdtype(img_crop.dtype, np.integer) else 1.
    n_h = 3
    n_w = 3

    ft1 = coef_box * box_features(box) / float(max(h, w))
    ft2 = coef_clas * clas / float(n_classes)
    ft3 = coef_embed * (img_embedding(img_crop, n_h, n_w) / div_embed).flatten()[None, :]
    # print(ft1.shape, ft2.shape, ft3.shape)
    features = np.hstack([ft1, ft2, ft3])
    return features

def draw_labels(frame, y, boxes, classes, id_colors):
    i = 0
    frame_labeled = np.float32(frame)
    for id, box, cls in zip(y, boxes, classes):
        # print("id", id)
        x1, y1, x2, y2 = box
        color = tuple(int(x) for x in id_colors[id])
        frame_labeled = cv2.rectangle(frame_labeled, (x1, y1), (x2, y2), color, 4)
        frame_labeled = cv2.putText(frame_labeled, f"obj {id} (class {cls})", (x1, y1-10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, color, 2)
        i += 1
    # print(f"drew {i}/{len(boxes)} objects")
    return frame_labeled