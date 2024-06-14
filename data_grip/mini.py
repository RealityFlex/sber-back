# file_uploader.py MinIO Python SDK example
from minio import Minio
from minio.error import S3Error
import io
from datetime import timedelta
from minio.deleteobjects import DeleteObject
from minio.commonconfig import REPLACE, CopySource

client = Minio(
    "62.109.8.64:9000",
    access_key="avJK24DY6nu1EP77ds3q",
    secret_key="fm6OwIdWz5GUh41yzUfGTZMnsTOFSfPPLhEcSLgJ",
    secure=False,
)

def download_data(bucket, filepath, source):
    # Get data of an object.
    client.fget_object(bucket, filepath, source)

# def load_data(bucket, filepath, source):
#     client.put_object(bucket, filepath, io.BytesIO(f'{source}'.encode()), 5)

def load_data_bytes(bucket, filepath, bytes):
    url = client.put_object(bucket, filepath, io.BytesIO(bytes), length=len(bytes))
    return url

def list_objects(bucket, sub, df_name):
    result = {"folders": [], "files": []}
    delimiter = '/'
    prefix=f"{sub}/{df_name}/"
    try:
        objects = client.list_objects(bucket, prefix=prefix)
        for obj in objects:
            # Если объект - это папка
            if obj.is_dir:
                folder_name = obj.object_name[len(prefix):].rstrip(delimiter)
                result["folders"].append(folder_name)
            else:
                file_name = obj.object_name[len(prefix):]
                result["files"].append(file_name)
    except S3Error as e:
        print("Error occurred.", e)
    
    return result

def list_files(bucket, sub, df_name):
    result = []
    try:
        objects = client.list_objects(bucket, prefix=f"{sub}/{df_name}/")
        for obj in objects:
            if not obj.is_dir:
                file_name = obj.object_name[len(f"{sub}/{df_name}/"):]
                result.append(file_name)
                
    except S3Error as e:
        print("Error occurred.", e)
    
    return result

def delete_file(bucket, sub, df_name, filename):
    error = client.remove_object(bucket, f"{sub}/{df_name}/{filename}"
    )
    return error

def presigned_get_object(bucket, filepath):
    url = client.presigned_get_object(
                bucket, filepath, expires=timedelta(hours=2)
                )
    return url