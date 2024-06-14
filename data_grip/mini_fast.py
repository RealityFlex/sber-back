import io
from datetime import timedelta
from miniopy_async import Minio
from miniopy_async.error import S3Error
from miniopy_async.deleteobjects import DeleteObject
from miniopy_async.commonconfig import REPLACE, CopySource
import asyncio
import pandas

client = Minio(
    "62.109.8.64:9000",
    access_key="avJK24DY6nu1EP77ds3q",
    secret_key="fm6OwIdWz5GUh41yzUfGTZMnsTOFSfPPLhEcSLgJ",
    secure=False,
)

async def download_data(bucket, filepath, source):
    # Get data of an object.
    await client.fget_object(bucket, filepath, source)

async def load_df(bucket, filepath, df):
    excel_data = io.BytesIO()
    df.to_excel(excel_data, index=False)
    excel_data.seek(0)
    await client.put_object(bucket, filepath, excel_data, len(excel_data.getvalue()))

async def load_data_bytes(bucket, filepath, bytes):
    url = await client.put_object(bucket, filepath, io.BytesIO(bytes), length=len(bytes))
    return url

async def list_objects(bucket, sub, df_name):
    result = {"folders": [], "files": []}
    delimiter = '/'
    prefix = f"{sub}/{df_name}/"
    try:
        objects = await client.list_objects(bucket, prefix=prefix, recursive=True)
        async for obj in objects:
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

async def list_files(bucket, sub, df_name):
    result = []
    try:
        objects = await client.list_objects(bucket, prefix=f"{sub}/{df_name}/", recursive=True)
        for obj in objects:
            if not obj.is_dir:
                file_name = obj.object_name[len(f"{sub}/{df_name}/"):]
                result.append({"id":obj.etag, "filename":file_name})
    except S3Error as e:
        print("Error occurred.", e)
    return result

async def list_only_files(bucket, sub, df_name):
    result = []
    try:
        objects = await client.list_objects(bucket, prefix=f"{sub}/{df_name}/", recursive=True)
        for obj in objects:
            if not obj.is_dir:
                file_name = obj.object_name[len(f"{sub}/{df_name}/"):]
                result.append(file_name)
    except S3Error as e:
        print("Error occurred.", e)
    return result

async def delete_file(bucket, filename):
    error = await client.remove_object(bucket, filename)
    return error

async def presigned_get_object(bucket, filepath):
    url = await client.presigned_get_object(
        bucket, filepath, expires=timedelta(hours=2)
    )
    return url

async def copy(bucket, oject, source_backet, source_object):
    await client.copy_object(
        bucket,
        oject,
        CopySource(source_backet, source_object)
    )