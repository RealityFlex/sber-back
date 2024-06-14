import uvicorn
from fastapi import FastAPI, File, UploadFile, status, Header, Request, Depends, BackgroundTasks, Body, HTTPException
from apscheduler.schedulers.background import BackgroundScheduler
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.encoders import jsonable_encoder
from tables_fast import Table
from pydantic import BaseModel
from typing import Union, List, Optional, Annotated, Dict, Any
# import mini
import json
import read_data_fast as read_data
import asyncio
import db_w as db
import uuid
# import pandas as pd
from tasks import celery_use_filter, celery_get_rows, celery_get_table, get_res
HeaderParameter = Annotated[Union[str, None], Header()]
app = FastAPI()

origins = [
    "*",
]

tb = Table()
# tb.init()

class Value(BaseModel):
    key: str
    filter: Union[str, None] = None
    expression: Union[str, None] = None
    value: Union[str, None] = None
    sub: Optional[List['Value']] = None

class Sort(BaseModel):
    keys: List[str]
    ascending: bool = True
    find: str = None

class Edit(BaseModel):
    row: List[int]
    column: str = None
    value: str

# class ValueList(BaseModel):
#     data: List[Value]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

tasks: Dict[str, Dict[str, Any]] = {}

async def load_data(sub, df_name):
    await read_data.load_df(sub, df_name)
    

@app.get("/get_table")
async def getT(exp: Optional[str] = Header(None), sub: Optional[str] = Header(None), n: int = 10, pg: int = 0, df_name: str = 'bills'):
    read_data.add_user(exp, sub)
    df = read_data.get_df(sub, df_name)
    if df.empty:
        return "Таблица не загружена"
    else:
        total_rows = len(df)
        total_pages = (total_rows) // n
        start_idx = pg * n
        end_idx = start_idx + n
        if end_idx > total_rows-1:
            end_idx = total_rows
        data = df.iloc[start_idx:end_idx].to_dict('records')
    return {
                "meta": {
                    "n": n,
                    "pg": pg,
                    "pages": total_pages
                },
                "data": data}

@app.post("/sort")
async def sortT(sort: Sort, exp: Optional[str] = Header(None), sub: Optional[str] = Header(None), n: int = 10, pg: int = 0, df_name: str = 'bills'):
    read_data.add_user(exp, sub)
    df = read_data.get_df(sub, df_name)
    if df.empty:
        return "Таблица не загружена"
    else:
        df = df.sort_values(by=sort.keys, ascending=sort.ascending)

        if sort.find:
        # Преобразуем указанные колонки в строковый тип для поиска
            df_cp = df[sort.keys].astype(str)
            # Формируем маску для поиска
            mask = df_cp.apply(lambda row: row.str.contains(sort.find, na=False).any(), axis=1)
            # Фильтруем DataFrame по маске
            df = df[mask]
        df_name = df_name+"_edit"
        start_idx = pg * n
        end_idx = start_idx + n
        data = df.iloc[start_idx:end_idx].to_dict('records')
        read_data.set_df(sub, df_name, df)
    return data

@app.post("/edit_cell")
async def edit_C(edit: Edit, exp: Optional[str] = Header(None), sub: Optional[str] = Header(None), n: int = 10, pg: int = 0, df_name: str = 'bills'):
    read_data.add_user(exp, sub)
    df_name = df_name+"_edit"
    df = read_data.get_df(sub, df_name)
    if df.empty:
        return "Таблица не загружена"
    else:
        try:
        # Получаем индексы строк и столбцов
            row_idx = edit.row
            col_idx = edit.column
            # Если value == 'del' и column == None, удаляем ячейку
            if edit.value == 'del' and edit.column is None:
                df = df.drop(row_idx).reset_index(drop=True)
            # В противном случае, преобразовываем значение к типу данных в ячейке
            else:
                for i in row_idx:
                    dtype = df[col_idx].dtype  # Get the dtype of the column
                    df.at[i, col_idx] = dtype.type(edit.value)
                
        except Exception as e:
            print(f"Error editing DataFrame: {e}")
            return f"Error editing DataFrame: {e}"
        start_idx = pg * n
        end_idx = start_idx + n
        data = df.iloc[start_idx:end_idx].to_dict('records')
    read_data.set_df(sub, df_name, df)
    return data

@app.get("/pre_load_table")
async def getT(exp: HeaderParameter, sub: HeaderParameter, n:int=10, pg:int=0, df_name='bills'):
    read_data.add_user(exp, sub)
    asyncio.create_task(load_data(sub, df_name))
    return {"message": "Загрузка данных началась"}

@app.get("/list_files")
async def list_files(exp: HeaderParameter, sub: HeaderParameter, df_name='bills'):
    return await read_data.get_list_files(sub,df_name)

@app.post("/filter")
async def filterR(exp: HeaderParameter, sub: HeaderParameter, data: List[Value], df_name='bills'):
    read_data.add_user(exp, sub)
    # asyncio.create_task(tb.use_filter(data=jsonable_encoder(data), sub=sub, 
    #                                     df_name=df_name, df_real=read_data.get_df(sub, df_name)))
    task_id = str(uuid.uuid4())
    tasks[task_id] = {"status": "in_progress", "result": None}

    async def task_wrapper():
        try:
            result = await tb.use_filter(data=jsonable_encoder(data), sub=sub, df_name="filter", df_real=read_data.get_df(sub, df_name))
            tasks[task_id]["status"] = "completed"
            tasks[task_id]["result"] = result
        except Exception as e:
            tasks[task_id]["status"] = "failed"
            tasks[task_id]["result"] = str(e)
    
    asyncio.create_task(task_wrapper())

    return {"message": "Задача улетела", 'id':task_id}

@app.get("/status/{task_id}")
async def get_status(task_id: str):
    if task_id not in tasks:
        raise HTTPException(status_code=404, detail="Task not found")
    
    return tasks[task_id]

@app.post("/load_table")
async def loadT(exp: HeaderParameter, sub: HeaderParameter, file: UploadFile, df_name='bills'):
    print(exp, sub)
    read_data.add_user(exp, sub)
    filename = file.filename
    file = await file.read()
    asyncio.create_task(read_data.upload_tb_df(sub, df_name, f"{sub}/{df_name}/{filename}", file))

@app.delete("/delete_table")
async def delT(exp: HeaderParameter, sub: HeaderParameter, filename, df_name='bills'):
    read_data.add_user(exp, sub)
    asyncio.create_task(read_data.delete_tb_df(sub, df_name, filename))

@app.post('/add_config', summary='Get history of currently logged in user')
async def add_config(exp: HeaderParameter, sub: HeaderParameter, data = Body()):
    read_data.add_user(exp, sub)
    conf = db.add_new_configuration(sub, data)
    return conf

@app.get('/history', summary='Get history of currently logged in user')
async def get_history(exp: HeaderParameter, sub: HeaderParameter):
    read_data.add_user(exp, sub)
    conf = db.get_user_configurations(sub)
    if conf == None:
         pass
    return conf

@app.get('/distribution/{config_id}', summary='Get history of currently logged in user')
async def get_history(exp: HeaderParameter, sub: HeaderParameter, config_id):
    conf = db.get_user_configuration(config_id)
    if conf == None:
         pass
    return conf

@app.get('/task_status/{task_id}')
async def task_status(task_id: str):
    task = await get_res(task_id)
    if task.state == 'PENDING':
        response = {
            "status": "PENDING",
            "result": None
        }
    elif task.state != 'FAILURE':
        res = task.result
        if "sub" in res and "df_name" in res:
            asyncio.create_task(load_data(res['sub'],res['df_name']))
            response = {
                "status": task.state,
                "result": task.result
            }
        else:
            response = {
                "status": task.state,
                "result": task.result
            }
    else:
        response = {
            "status": "FAILURE",
            "result": str(task.info),  # task.info содержит исключение, если задача не выполнена
        }
    return response