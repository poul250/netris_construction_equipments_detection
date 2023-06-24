import uvicorn
import uuid
import argparse
import pathlib
import os
from typing import List
from fastapi import FastAPI, File, UploadFile, Response
from clients import VideoServiceClient
from pydantic import BaseModel


app = FastAPI()

base_dir: pathlib.Path = '/Users/pavelkulis/prog/hackaton/data'

video_service: VideoServiceClient = None


def make_uid() -> str:
    return str(uuid.uuid4())

@app.post("/upload")
def upload(file: UploadFile = File(...)):
    task_id = make_uid()
    file_name = "src.mp4"

    task_dir = base_dir / task_id
    task_dir.mkdir(parents=True, exist_ok=True)

    file_path = task_dir / file_name

    try:
        contents = file.file.read()
        with open(file_path, 'wb') as f:
            f.write(contents)
    except Exception as exc:
        print(exc)
        return Response(status_code=500)
    finally:
        file.file.close()

    # try:
    #     video_service.process(
    #         task_id=task_id,
    #         work_dir=str(task_dir),
    #         file_name=file_name,
    #         src_path=file_path,
    #     )
    # except Exception as exc:
    #     print(exc)
    #     return Response(status_code=500)

    return {"task_id": task_id}


class GetResultRequest(BaseModel):
    task_id: str

class GetResultResponse(BaseModel):
    task_id: str

@app.post("/get_result")
def get_result(request: GetResultRequest) -> dict:
    task_id = request.task_id

    task_dir = base_dir / task_id
    ok_path = task_dir / 'ok'
    if ok_path.exists():
        # TODO: some results
        return {}

    return


def parse_args():
    global base_dir
    global video_service

    base_dir = pathlib.Path(os.environ['DATA_DIR'])
    if not base_dir:
        print("Failed to get base dir")
        exit(-1)

    video_service_port = os.environ['VIDEO_SERVICE_PORT']
    if not video_service_port:
        print("Failed to get video service port")
        exit(-1)

    video_service = VideoServiceClient(
        host='http://localhost',
        port=int(video_service_port)
    )

    parser = argparse.ArgumentParser()
    parser.add_argument('base-dir')


def main():
    parse_args()
    uvicorn.run(app, host="0.0.0.0", port=8000)

if __name__ == "__main__":
    main()
