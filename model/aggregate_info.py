import numpy as np
from typing import List
from pydantic import BaseModel

def rolling_aggregation(a, window, axis=1, function="min"):
    shape = a.shape[:-1] + (a.shape[-1] - window + 1, window)
    strides = a.strides + (a.strides[-1],)
    rolling = np.lib.stride_tricks.as_strided(a, shape=shape, strides=strides)
    if function == "min":
        return np.min(rolling, axis=axis)
    elif function == "max":
        return np.max(rolling, axis=axis)
    elif function == "mean":
        return np.mean(rolling, axis=axis)

# keep output size the same as input by padding input on the left
def rolling_aggregation_ext_left(a, window, axis=1, function="min"):
    return rolling_aggregation(np.pad(a, (window-1, 0), 'edge'), window, axis=1, function="min")

"""
returns: list of (start, end) tuples. boundary format: [start, end)
"""
def get_const_val_intervals(arr):
    intervals = []
    a_deltas = arr[1:]-arr[:-1]
    change_idx = np.where(a_deltas != 0)[0] + 1
    change_idx = np.concatenate(([0], change_idx, [len(arr)]))
    for i in range(len(change_idx)-1):
        start, end = change_idx[i], change_idx[i+1]
        value = arr[start]
        intervals.append((start, end))
    return intervals

# intervals == get_const_val_intervals(arr)
# if interval is too short, fill it in arr with value from latest long enough interval. return modified arr
def fix_short_intervals(arr, intervals):
    min_event_len = 20
    intervals_new = []
    val_good_prev = None
    arr_copy = np.copy(arr)
    for start, end in intervals:
        val = arr[start]
        if end - start < min_event_len:
            if val_good_prev is not None:
                arr_copy[start:end] = val_good_prev
        else:
            val_good_prev = val
    return arr_copy

"""
return dict: object id -> array[n_frames, 8] of this object's features for ALL frames,
including those where it's absent.
features are presence in frame (0/1) and 7 features in final_fts_list's format
"""
def get_id_histories(final_fts_list, ids):
    id_histories = dict()
    for id in ids:
        obj_fts = None
        id_history = np.zeros((len(final_fts_list), 8), dtype='float')
        for i, final_fts in enumerate(final_fts_list):
            obj_fts_idx = np.where(final_fts[:, 4].astype(int).flatten() == id)[0]
            if len(obj_fts_idx) == 0:
                # obj is absent in frame i
                is_present = 0.
                if obj_fts is not None:
                    last_fts = obj_fts[-7:]
                else:
                    last_fts = np.array([10000, 10000, -1, -1, id, -1, 0.0]).astype(float)
            else:
                # assert(len(obj_fts_idx) == 1)
                if(len(obj_fts_idx) > 1):
                    print(i, "multiple duplicates of the same id in one frame! TODO FIX")
                is_present = 1.
                last_fts = np.copy(final_fts[obj_fts_idx[0]])
            obj_fts = np.concatenate((np.array([is_present]), last_fts))
            id_history[i] = obj_fts
        id_histories[id] = id_history
    return id_histories

"""
rolling aggregation on id_history arrays, so its presence and other features will be more consistent (less flickering)
"""
def blur_id_histories(id_histories, window=30):
    ids = sorted(id_histories.keys())
    id_histories_out = dict()
    for id in ids:
        id_history = np.copy(id_histories[id])
        id_history[:, 0] = rolling_aggregation_ext_left(id_history[:, 0], window, function="max") # presence
        id_history[:, 1] = rolling_aggregation_ext_left(id_history[:, 1], window, function="min") # x1
        id_history[:, 2] = rolling_aggregation_ext_left(id_history[:, 2], window, function="min") # y1
        id_history[:, 3] = rolling_aggregation_ext_left(id_history[:, 3], window, function="max") # x2
        id_history[:, 4] = rolling_aggregation_ext_left(id_history[:, 4], window, function="max") # y2
        # id_history[:, 5] = rolling_aggregation_ext_left(id_history[:, 5], window, function="min") # id
        # id_history[:, 6] = rolling_aggregation_ext_left(id_history[:, 6], window, function="min") # class
        id_history[:, 7] = rolling_aggregation_ext_left(id_history[:, 7], window, function="mean") # confidence
        id_histories_out[id] = id_history
    return id_histories_out

def aggregate_id_history(id_history):
    fts = np.zeros(11, dtype='float')
    fts[0] = id_history[0, 0] # presence
    fts[1] = np.min(id_history[:, 1]) # x1
    fts[2] = np.min(id_history[:, 2]) # y1
    fts[3] = np.max(id_history[:, 3]) # x2
    fts[4] = np.max(id_history[:, 4]) # y2
    fts[5] = id_history[0, 5] # id
    fts[6] = (id_history[:, 6][id_history[:, 6] >= 0])[0] # class
    fts[7] = np.mean(id_history[:, 7]) # confidence

    # calculate how much the object was moving
    boxes = id_history[:, 1:5]
    box_centers = (boxes[:, 0:2] + boxes[:, 2:4]) / 2.
    box_sizes = (boxes[:, 2:4] - boxes[:, 0:2])
    # normalize by box size
    divisors = box_sizes.mean(axis=1).reshape(-1, 1)
    divisors += 1e-2
    box_centers /= divisors
    box_sizes /= divisors
    box_deltas_c = box_centers[:-1] - box_centers[1:]
    box_deltas_s = box_sizes[:-1] - box_sizes[1:]
    window = 10
    box_deltas_c = rolling_aggregation_ext_left(box_centers, window, function="mean")
    box_deltas_s = rolling_aggregation_ext_left(box_sizes, window, function="mean")
    box_deltas_c = np.abs(box_deltas_c)
    box_deltas_s = np.abs(box_deltas_s)
    box_center_path = np.mean(box_deltas_c)
    box_size_path = np.mean(box_deltas_s)
    fts[8] = box_center_path
    fts[9] = box_size_path


    # parameters (constants)
    center_path_thres = 20.0
    size_path_thres = 0.3
    center_path_coef = 1.0
    size_path_coef = 1.0
    bias = 0.9

    is_working_raw = (
        center_path_coef * float(box_center_path > center_path_thres)
        + size_path_coef * float(box_size_path > size_path_thres)
    ) * bias / (center_path_coef + size_path_coef)
    is_working = bool(round(is_working_raw))
    fts[10] = float(is_working)
    # print("paths:", box_center_path, box_size_path, '=>', is_working_raw, is_working)
    return fts

class EventsList(BaseModel):
    object_id: str
    object_type: str
    is_present: List[bool]
    is_working: List[bool]
    left_x: List[int]
    left_y: List[int]
    right_x: List[int]
    right_y: List[int]
    start_time: List[int]
    end_time: List[int]

# returns dict[str, EventsList]: object id -> EventsList (all events for this object, including where it's not present)
def get_events(id_histories) -> dict[str, EventsList]:
    events_lists = dict()
    ids = sorted(id_histories.keys())
    events = dict()
    for id in ids:
        id_history = id_histories[id]
        # get intervals of constant presence or absence
        a = id_history[:, 0].flatten()
        intervals0 = get_const_val_intervals(a)
        a2 = fix_short_intervals(a, intervals0)
        id_history[:, 0] = a2
        intervals = get_const_val_intervals(a2)
        # print("----", intervals0, intervals)
        cls0 = None
        events_list = EventsList(object_id=str(id), object_type='',
                                 is_present=[], is_working=[],
                                 left_x=[], left_y=[], right_x=[], right_y=[],
                                 start_time=[], end_time=[])
        for start, end in intervals:
            hist = id_history[start:end]
            assert(len(hist) > 0)
            fts = aggregate_id_history(hist)
            start_time = int(start)
            end_time = int(end - 1)
            is_present = bool(round(fts[0]))
            x1 = int(round(fts[1]))
            y1 = int(round(fts[2]))
            x2 = int(round(fts[3]))
            y2 = int(round(fts[4]))
            # id = round(fts[5])
            cls = int(round(fts[6]))
            is_working = bool(round(fts[10]))
            if not is_present:
                is_working = False
                x1, y1, x2, y2 = 0, 0, 2560, 1440
            if cls0 is None:
                if cls >= 0:
                    cls0 = cls
                    events_list.object_type = str(cls)
            events_list.is_present.append(is_present)
            events_list.is_working.append(is_working)
            events_list.left_x.append(x1)
            events_list.left_y.append(y1)
            events_list.right_x.append(x2)
            events_list.right_y.append(y2)
            events_list.start_time.append(start_time)
            events_list.end_time.append(end_time)
        if events_list.is_present == [False]:
            continue
        events_lists[str(id)] = events_list
    return events_lists

def get_events_lists_from_fts(final_fts_list, max_id):
    ids = list(range(0, max_id+1))
    id_histories = get_id_histories(final_fts_list, ids)

    blur_window = 60

    id_histories = blur_id_histories(id_histories, window=blur_window)
    events_lists: dict[str, EventsList] = get_events(id_histories)
    return events_lists
