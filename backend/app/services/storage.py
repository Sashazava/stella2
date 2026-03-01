import uuid
from datetime import timedelta
from minio import Minio
from minio.error import S3Error

BUCKET_LISTINGS = "stella-listings"
BUCKET_AVATARS = "stella-avatars"


def init_minio(endpoint: str, access_key: str, secret_key: str, secure: bool = False) -> Minio:
    """Create MinIO client for internal operations."""
    return Minio(endpoint, access_key=access_key, secret_key=secret_key, secure=secure)


def init_minio_public(server_url: str, access_key: str, secret_key: str) -> Minio:
    """Create MinIO client configured with public-facing URL for presigned URLs."""
    from urllib.parse import urlparse
    parsed = urlparse(server_url)
    secure = parsed.scheme == "https"
    endpoint = parsed.netloc
    return Minio(endpoint, access_key=access_key, secret_key=secret_key, secure=secure)


def ensure_buckets(client: Minio) -> None:
    """Idempotently create required buckets."""
    for bucket in [BUCKET_LISTINGS, BUCKET_AVATARS]:
        if not client.bucket_exists(bucket):
            client.make_bucket(bucket)


def get_upload_url(client: Minio, bucket: str, object_key: str, expires_hours: int = 2) -> str:
    """Generate presigned PUT URL for direct browser upload."""
    return client.presigned_put_object(
        bucket, object_key, expires=timedelta(hours=expires_hours)
    )


def get_download_url(client: Minio, bucket: str, object_key: str, expires_hours: int = 1) -> str:
    """Generate presigned GET URL for viewing."""
    return client.presigned_get_object(
        bucket, object_key, expires=timedelta(hours=expires_hours)
    )


def delete_object(client: Minio, bucket: str, object_key: str) -> None:
    client.remove_object(bucket, object_key)


def delete_objects_by_prefix(client: Minio, bucket: str, prefix: str) -> None:
    """Delete all objects with given prefix."""
    from minio.deleteobjects import DeleteObject
    objects = client.list_objects(bucket, prefix=prefix, recursive=True)
    delete_list = [DeleteObject(obj.object_name) for obj in objects]
    if delete_list:
        errors = list(client.remove_objects(bucket, delete_list))
        if errors:
            raise S3Error(f"Failed to delete some objects: {errors}")


def generate_object_key(user_id: str, filename: str) -> str:
    """Generate unique object key: {user_id}/{uuid}.{ext}"""
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else "bin"
    return f"{user_id}/{uuid.uuid4()}.{ext}"
