from pathlib import Path
from uuid import uuid4

from fastapi import UploadFile

from app.core.config import settings


ALLOWED_CSV_CONTENT_TYPES = {
    "text/csv",
    "application/csv",
    "application/vnd.ms-excel",
}

CHUNK_SIZE_BYTES = 1024 * 1024


class InvalidFileError(ValueError):
    pass


class FileTooLargeError(ValueError):
    pass

async def save_csv_file(file: UploadFile) -> tuple[str, int]:
    original_filename = Path(file.filename or "").name

    if not original_filename:
        raise InvalidFileError("A filename is required")

    if Path(original_filename).suffix.lower() != ".csv":
        raise InvalidFileError("Only CSV files are allowed")

    if file.content_type not in ALLOWED_CSV_CONTENT_TYPES:
        raise InvalidFileError("Invalid CSV content type")

    settings.upload_dir.mkdir(parents=True, exist_ok=True)

    stored_filename = f"{uuid4().hex}.csv"
    destination = settings.upload_dir / stored_filename
    size_bytes = 0

    try:
        with destination.open("xb") as output_file:
            while chunk := await file.read(CHUNK_SIZE_BYTES):
                size_bytes += len(chunk)

                if size_bytes > settings.max_upload_size_bytes:
                    raise FileTooLargeError(
                        "File exceeds the maximum allowed size"
                    )

                output_file.write(chunk)

        if size_bytes == 0:
            raise InvalidFileError("CSV file is empty")

    except Exception:
        destination.unlink(missing_ok=True)
        raise

    finally:
        await file.close()

    return stored_filename, size_bytes

def delete_stored_file(stored_filename: str) -> None:
    safe_filename = Path(stored_filename).name
    file_path = settings.upload_dir / safe_filename
    file_path.unlink(missing_ok=True)