import os
import cv2
import time
import json
import ffmpeg
import uvicorn
import requests
from aggregate_info import *
from detect_for_image import Detector
from track import *
from typing import List
from pydantic import BaseModel
from fastapi import FastAPI, BackgroundTasks


app = FastAPI()
HEADERS = {'Content-type': 'application/json'}
TARGET_FPS = 5
detector = Detector("best.pt", "0", 1504, 0.25, 0.45)

service_port:int = 8000


class Request(BaseModel):
    task_id: str
    format: str
    path: str

async def _process_video(req: Request):
    video = cv2.VideoCapture(f"{req.path}/src.{req.format}")

    n_last_frames = 16
    dist_thres = 6.

    last_X = deque()
    last_y = deque()
    max_id = -1

    final_fts_list = []
    skip_frames = 6 // TARGET_FPS

    counter = 0
    while True:
        ret, frame = video.read()
        counter += 1
        if counter % skip_frames == 0:
            box_features_raw = detector.detect(frame)
            y_prev = None
            if len(box_features_raw) == 0:
                X = np.array([])
                y_nonew = np.array([], dtype=int)
            else:
                box_features_raw = box_features_raw[0]
                # print("boxes shape:", box_features_raw.shape)
                n_boxes = len(box_features_raw)
                boxes = np.round(box_features_raw[:, 0:4]).astype(int)
                confidence = box_features_raw[:, 4:5] # not using yet
                classes = box_features_raw[:, 5:6].astype(int)
                # imgs_crop = [crop_box(img, box) for box in boxes]

                # print(boxes[0][None, :].shape, np.array(classes[0])[None, :].shape)
                # get features for matching
                X = np.array([make_all_features(boxes[i][None, :], np.array(classes[i])[None, :], frame).flatten() for i in range(n_boxes)])
                # print("X:", X.shape)
                if len(last_y) == 0:
                    y_nonew = -np.ones(X.shape[0], dtype=int)
                else:
                    X_prev = list(last_X)
                    y_prev = list(last_y)
                    # print("Aaa:", X_prev.shape, y_prev.shape)
                    # y = match_ids_single(X_prev[-1], X, y_prev[-1], dist_thres=dist_thres)
                    y_nonew = match_ids_multi(X_prev, X, y_prev, dist_thres=dist_thres)
                    # print("y_nonew", y_nonew.dtype)
            y, max_id = make_new_ids(y_nonew, max_id)
            # print("y", y.dtype)
            # print("y match result:\n", y_prev if y_prev is not None else '')
            # print(y_nonew)
            # print(y)
            last_X.append(X)
            last_y.append(y)
            if len(last_X) > n_last_frames:
                last_X.popleft()
                last_y.popleft()
            final_fts = np.hstack([boxes, y.reshape(-1, 1), classes.reshape(-1, 1), confidence.reshape(-1, 1)]).astype(float)
            final_fts_list.append(final_fts)
        if not ret:
            break
    events_lists: dict[str, EventsList] = get_events_lists_from_fts(final_fts_list, max_id)

    with open(f"{req.path}/info.json", "w") as f:
        json.dump([r.dict() for r in events_lists.values()], f)


def init():
    global service_port

    service_port_raw = os.environ['MODEL_SERVICE_PORT']
    if not service_port_raw:
        print("Failed to find model service port, using default")
    else:
        service_port = int(service_port_raw)


@app.post("/process_video")
async def process_video(req: Request, background_tasks: BackgroundTasks) -> None:
    background_tasks.add_task(_process_video, req)


def main():
    init()
    uvicorn.run(app, host="0.0.0.0", port=service_port)

if __name__ == "__main__":
    main()
