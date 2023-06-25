import uvicorn
import uuid
import pathlib
import os
import json
from typing import Dict, List
from fastapi import FastAPI, File, UploadFile, Response, Header
from fastapi.responses import StreamingResponse, HTMLResponse, RedirectResponse
from clients import VideoServiceClient
from pydantic import BaseModel
import starlette.status as status


VIDEO_CHUNK_SIZE = 1024 * 1024  # 1 Mb
INFO_FILE = "info.json"
OK_FILE = "ok"

app = FastAPI()

base_dir: pathlib.Path = '/Users/pavelkulis/prog/hackaton/data'

video_service: VideoServiceClient = None

runtime_port: int = None


def make_uid() -> str:
    return str(uuid.uuid4())


def _check_task_done(task_dir: pathlib.Path) -> bool:
    ok_path = task_dir / OK_FILE
    return ok_path.exists()

@app.get("/")
async def index():
    html_content = f"""
    <form method="post" action="http://localhost:{runtime_port}/upload" enctype="multipart/form-data">
        <label for="file">File</label>
        <input id="file" name="file" type="file" />
        <button>Upload</button>
    </form>
    """
    return HTMLResponse(content=html_content, status_code=200)


@app.post("/upload")
async def upload(file: UploadFile = File(...)):
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

    try:
        video_service.process(
            task_id=task_id,
            work_dir=str(task_dir),
            src_path=str(file_path),
            file_name=file_name
        )
    except Exception as exc:
        print(exc)
        return Response(status_code=500)

    return RedirectResponse(f"/wait_result?task_id={task_id}", status_code=303)


class GetResultRequest(BaseModel):
    task_id: str


class GetResultEvent(BaseModel):
    start: int
    end: int
    video_timestamp: int
    status: str

class GetResultObject(BaseModel):
    url: str
    type: str
    timeline: List[GetResultEvent]


def build_objects(info: dict) -> Dict[str, GetResultObject]:
    return []

def make_file_url(local_path: pathlib.Path) -> str:
    return f'http://localhost:'


@app.get("/wait_result")
async def wait_result(task_id: str):
    task_dir = base_dir / task_id

    if _check_task_done(task_dir):
        return RedirectResponse(f"/get_result?task_id={task_id}", status_code=303)

    html_content = """
    Waiting...
    <meta http-equiv="refresh" content="5">
    """

    return HTMLResponse(html_content, status_code=200)


@app.get("/get_result")
async def get_result(task_id: str, response: Response):
    task_dir = base_dir / task_id
    if not _check_task_done(task_dir):
        return Response(status=425)

    info_json = task_dir / INFO_FILE
    if not info_json.exists():
        print('Info json not exists')
        return Response(status_code=500)

    with open(info_json, 'r') as f:
        info = json.load(f)

    response.headers['Content-Type'] = 'application/json'
    return info


class GetInfoRequest(BaseModel):
    task_id: str

@app.get("/info")
async def get_info(data: GetInfoRequest):
    task_id = data.task_id

    task_dir = base_dir / task_id
    if not task_dir.exists():
        print("Task dir doesn't exist")
        return Response(status_code=404)

    if not _check_task_done(task_dir):
        print("Task is not done")
        return Response(status_code=425)

    info_file = task_dir / INFO_FILE
    if not info_file.exists():
        print("Info file doesn't exist")
        return Response(status_code=500)

    with open(info_file, 'r') as f:
        return json.load(f)


class GetVideoRequest(BaseModel):
    task_id: str
    video_name: str


@app.get("/video")
async def get_video(data: GetVideoRequest, range: str = Header(None)):
    task_dir: pathlib.Path = base_dir / data.task_id

    if not task_dir.exists():
        return Response(status_code=404)

    video_path: pathlib.Path = task_dir / data.video_name
    if not video_path.exists():
        return Response(status_code=404)

    start, end = range.replace("bytes=", "").split("-")
    start = int(start)
    end = int(end) if end else start + VIDEO_CHUNK_SIZE
    with open(video_path, "rb") as video:
        video.seek(start)
        data = video.read(end - start)
        filesize = str(video_path.stat().st_size)

        headers = {
            'Content-Range': f'bytes {str(start)}-{str(end)}/{filesize}',
            'Accept-Ranges': 'bytes'
        }
        return Response(data, status_code=206, headers=headers, media_type="video/mp4")

def parse_args():
    global base_dir
    global video_service
    global runtime_port

    base_dir = pathlib.Path(os.environ['DATA_DIR'])
    if not base_dir:
        print("Failed to get base dir")
        exit(-1)

    runtime_port_raw = os.environ['RUNTIME_SERVICE_PORT']
    if not runtime_port_raw:
        print("Failed to get runtime service port")
        exit(-1)
    runtime_port = int(runtime_port_raw)

    video_service_port = os.environ['VIDEO_SERVICE_PORT']
    if not video_service_port:
        print("Failed to get video service port")
        exit(-1)

    video_service = VideoServiceClient(
        host='http://localhost',
        port=int(video_service_port)
    )


def main():
    parse_args()
    uvicorn.run(app, host="0.0.0.0", port=runtime_port)

if __name__ == "__main__":
    main()
