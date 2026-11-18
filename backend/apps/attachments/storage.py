"""
File contents live in MongoDB GridFS (bucket ``attachments``), next to the rest
of the data - no separate file server or disk folder to back up.

GridFS splits each file into 255 kB chunks:
``attachments.files`` holds one document per file, ``attachments.chunks`` the data.
"""

import gridfs
from django.db import connection

BUCKET_NAME = "attachments"


def bucket() -> gridfs.GridFSBucket:
    return gridfs.GridFSBucket(connection.database, bucket_name=BUCKET_NAME)


def put(stream, *, filename: str, content_type: str, metadata: dict):
    """Store a file and return its GridFS id."""
    stream.seek(0)
    return bucket().upload_from_stream(filename, stream, metadata={**metadata, "contentType": content_type})


def open(file_id):  # noqa: A001 - mirrors the GridFS wording
    """A read-only, file-like stream of the stored bytes."""
    return bucket().open_download_stream(file_id)


def exists(file_id) -> bool:
    return connection.database[f"{BUCKET_NAME}.files"].count_documents({"_id": file_id}, limit=1) > 0


def delete(file_id) -> None:
    try:
        bucket().delete(file_id)
    except gridfs.errors.NoFile:
        pass  # already gone
