import pandas as pd
import json
import time
import mini_fast as mini
import asyncio
import aiofiles
import io
from aiobotocore.session import get_session
from aiohttp import ClientSession

users = {}

async def async_read_excel(content):
    return pd.read_excel(io.BytesIO(content))

async def fetch_and_read_excel(session, url):
    async with session.get(url) as response:
        content = await response.read()
    return await async_read_excel(content)

def add_user(exp, user):
    if user not in users:
        users[user] = {'exp': int(exp)}
    else:
        users[user]['exp'] = int(exp)



async def save_df_to_minio(user, table, df):
    try:        
        # Upload Excel file to MinIO
        object_name = f"{user}/{table}/1.xlsx"
        await mini.load_df('user-tabels', object_name, df)
        
        print(f"DataFrame saved as {object_name} in MinIO.")
        return object_name
    
    except Exception as e:
        print(f"Error uploading DataFrame to MinIO: {e}")
        return None

def get_df(user, df_name):
    if user in users:
        if df_name in users[user]:
            return users[user][df_name]
        else:
            return pd.DataFrame()
    else:
        return pd.DataFrame()
    
async def load_df(user, df_name):
    df = pd.DataFrame()
    arr = ['list_contracts.xlsx','main_assets.xlsx',' service_codes.xlsx']
    async with ClientSession() as session:
        file_list = await mini.list_only_files('user-tabels', user, df_name)
        if len(file_list) == 0:
            await mini.copy('user-tabels', f'{user}/{df_name}/low.xlsx', 'user-tabels', 'Default-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/bills/low_data.xlsx')
            file_list = await mini.list_only_files('user-tabels', user, df_name)

        hard_list = await mini.list_only_files('user-tabels', user, "hardcoded")
        for i in arr:
            if not i in hard_list:
                await mini.copy('user-tabels', f'{user}/{df_name}/{i}', 'user-tabels', 'Default-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/hardcoded/{i}')
        
        tasks = []
        for file in file_list:
            presigned_url = await mini.presigned_get_object('user-tabels', f'{user}/{df_name}/{file}')
            tasks.append(fetch_and_read_excel(session, presigned_url))
        
        # Выполняем все задачи асинхронно и ждем их завершения
        dataframes = await asyncio.gather(*tasks)

        # Конкатенируем все полученные DataFrame
        df = pd.concat(dataframes, ignore_index=True)

    df.replace([float('inf'), float('-inf'), float('nan')], 0, inplace=True)
    if user not in users:
        users[user] = {}
    users[user][df_name] = df
    users[user][f"{df_name}_edit"] = df
    print(df.info())
    return df

async def upload_tb_df(user, df_name, filename, file):
    df = get_df(user, df_name)
    print("upload", df.head())
    async with ClientSession() as session:
        await mini.delete_file("user-tabels", f"{user}/{df_name}/low.xlsx")
        t = await mini.list_files('user-tabels', user, df_name)
        if filename.split('/')[-1] in t:
            print("File exist")
            return {"error": "File exist"}

        await mini.load_data_bytes("user-tabels", filename, file)
        if filename.endswith('.csv'):
            dataframes = pd.read_csv(file)
        elif filename.endswith(('.xls', '.xlsx')):
            dataframes = pd.read_excel(file)
        else:
            return {"error": "Unsupported file format. Only CSV or Excel files are supported."}

        # Конкатенируем все полученные DataFrame
        df = pd.concat([df, dataframes], ignore_index=True)
        print(df.info())

    df.replace([float('inf'), float('-inf'), float('nan')], 0, inplace=True)
    if user not in users:
        users[user] = {}
    users[user][df_name] = df
    users[user][f"{df_name}_edit"] = df

async def delete_tb_df(user, df_name, filename):
    await mini.delete_file("user-tabels", f"{user}/{df_name}/{filename}")
    print("delete", filename)
    await load_df(user, df_name)
    print("delete", filename)

def set_df(user, table, df):
    if user in users:
        users[user][table] = df
    else:
        users[user] = {table: df}

def remove_expired_users():
    current_time = int(time.time())
    expired_users = [user for user, data in users.items() if data['exp'] is not None and data['exp'] < current_time]
    for user in expired_users:
        del users[user]

async def get_list_files(user, df_name):
    return await mini.list_files('user-tabels', user, df_name)