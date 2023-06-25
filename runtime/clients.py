import requests
import urllib.parse
import os
from pydantic import BaseModel


class ProcessRequest(BaseModel):
    task_id: str
    format: str
    path: str

class VideoServiceClient:
    def __init__(self, host: str, port: int) -> None:
        self._host = host
        self._port = port

    def process(self, task_id: str, work_dir: str, src_path: str, file_name: str) -> bool:
        url = urllib.parse.urljoin(f'{self._host}:{self._port}', 'process')
        _, ext = os.path.splitext(src_path)
        data = ProcessRequest(
            task_id=task_id,
            format=ext[1:],
            path=work_dir,
        )
        result = requests.post(url, json=data.dict())
        return result.ok
