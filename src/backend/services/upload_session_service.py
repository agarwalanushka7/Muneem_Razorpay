import uuid
from typing import Any


class UploadSessionService:

    def __init__(self):
        self.sessions: dict[str, dict[str, Any]] = {}

    def create_session(
        self,
        filename: str,
        file_type: str,
        data: Any,
    ) -> str:
        upload_id = str(uuid.uuid4())

        self.sessions[upload_id] = {
            "filename": filename,
            "file_type": file_type,
            "data": data,
        }

        return upload_id

    def get_session(
        self,
        upload_id: str,
    ):
        return self.sessions.get(upload_id)

    def delete_session(
        self,
        upload_id: str,
    ):
        self.sessions.pop(
            upload_id,
            None,
        )

    def exists(
        self,
        upload_id: str,
    ) -> bool:
        return upload_id in self.sessions


upload_session_service = UploadSessionService()