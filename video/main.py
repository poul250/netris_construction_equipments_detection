import os
import time
import json
import ffmpeg
import logging
import uvicorn
import requests
from collections import defaultdict
from typing import List, Dict, Any
from pydantic import BaseModel
from fastapi import FastAPI, BackgroundTasks

app = FastAPI()
TASK_TIMEOUT = 3600
CREATED_VIDEO_FPS = 5
SRC_VIDEO_FPS = 30
LARGE_INT = 2 ** 32
SMALL_INT = 0
headers = {'Content-type': 'application/json'}

service_port: int = None
model_service_port: int = None


class ProcessRequest(BaseModel):
    task_id: str
    format: str
    path: str


def process_video(req: ProcessRequest):  # затычка
    resp = requests.post(
        'http://localhost:{model_service_port}/process_video',
        json=req.json(),
        headers=headers
    )
    if not resp.ok:
        raise Exception('Failed to put ml service task')


class ObjectEventProperties(BaseModel):
    left_x: int = LARGE_INT
    left_y: int = LARGE_INT
    right_x: int = SMALL_INT
    right_y: int = SMALL_INT
    start_ts: int = LARGE_INT
    end_ts: int = SMALL_INT

def aggregate_events(events: Dict[str, Any]) -> Dict[str, ObjectEventProperties]:
    result =  defaultdict(ObjectEventProperties)
    for event in events:
        object_id = event["object_id"]
        result[object_id].left_x = min(result[object_id].left_x, min(event["left_x"]))
        result[object_id].left_y = min(result[object_id].left_y, min(event["left_y"]))
        result[object_id].right_x = max(result[object_id].right_x, max(event["right_x"]))
        result[object_id].right_y = max(result[object_id].right_y, max(event["right_y"]))
        result[object_id].start_ts = min(result[object_id].start_ts, min(event["start_ts"]))
        result[object_id].end_ts = max(result[object_id].end_ts, max(event["left_x"]))
    return result


async def _process(req: ProcessRequest):
    process_video(req)

    start_time = time.time()
    json_path = req.path + "/info.json"
    while True:
        time.sleep(1)
        if os.path.exists(json_path):
            with open(json_path, "r") as f:
                data = json.load(f)
            break
        if time.time() - start_time > TASK_TIMEOUT:
            raise Exception("Execution timeout")

    for object_id, properties in aggregate_events(data).items():
        output_file_path = f'{req.path}/{object_id}.{req.format}'
        if os.path.exists(output_file_path):
            os.remove(output_file_path)
        print(properties.dict())
        (
            ffmpeg
            .input(f"{req.path}/src.{req.format}")
            .trim(start=properties.start_ts, end=properties.end_ts) #TODO: плз проверь потом что диапазон имеют все норм с размерностями (тут и риски от меня и от Вани)
            .crop(
                x=properties.left_x,
                y=properties.left_y,
                width=properties.right_x - properties.left_x,
                height=properties.right_y - properties.left_y)
            .filter('fps', fps=CREATED_VIDEO_FPS, round='up')
            .output(output_file_path)
            .run()
        )
    open(f"{req.path}/ok", "w").close()


@app.post("/process")
async def process(req: ProcessRequest, background_tasks: BackgroundTasks) -> None:
    background_tasks.add_task(_process, req)
    return req


def init():
    global service_port
    global model_service_port

    service_port_raw = os.environ['VIDEO_SERVICE_PORT']
    if not service_port_raw:
        print("Failed to get runtime service port")
        exit(-1)
    service_port = int(service_port_raw)

    model_service_port_raw = os.environ['MODEL_SERVICE_PORT']
    if not model_service_port_raw:
        print("Failed to get runtime service port")
        exit(-1)
    model_service_port = int(model_service_port_raw)


def main():
    init()
    uvicorn.run(app, host="0.0.0.0", port=service_port)

if __name__ == "__main__":
    main()
