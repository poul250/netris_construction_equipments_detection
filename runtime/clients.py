import requests
import urllib.parse

class VideoServiceClient:
    def __init__(self, host: str, port: int) -> None:
        self._host = host
        self._port = port

    def process(self, task_id: str, work_dir: str, src_path: str, file_name: str) -> bool:
        url = urllib.parse.urljoin(f'{self._host}:{self._port}', 'process')
        data = {
            task_id: task_id,
            work_dir: work_dir,
            src_path: src_path,
            file_name: file_name,
        }
        result = requests.post(url, data=data)
        return result.ok
