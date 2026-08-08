from pydantic import BaseModel


class FolderScanRequest(BaseModel):
    folder_path: str


class DiscoveredVideoResponse(BaseModel):
    absolute_path: str
    relative_path: str
    size_bytes: int
    existing_srt: bool


class FolderScanResponse(BaseModel):
    videos: list[DiscoveredVideoResponse]


class FolderTranscribeRequest(BaseModel):
    folder_path: str
    video_paths: list[str]
    model_size: str
    language: str


class FolderTranscribeResponse(BaseModel):
    batch_id: str
    job_ids: list[str]
