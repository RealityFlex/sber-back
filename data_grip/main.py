# from __future__ import annotations
import uvicorn
from fastapi import FastAPI, File, UploadFile, status, Header, Request, Depends, BackgroundTasks, Body
from apscheduler.schedulers.background import BackgroundScheduler
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.encoders import jsonable_encoder
from tables import Table
from pydantic import BaseModel
from typing import Union, List, Optional, Annotated
import mini
import json
import read_data
import asyncio
import db_w as db
import pandas as pd
from tasks import send_email_report_dashboard, celery_use_filter, celery_get_rows, celery_get_table
HeaderParameter = Annotated[Union[str, None], Header()]
app = FastAPI()

# tb = Table("low_data.xlsx")

user_tables = {}

origins = [
    "*",
]

class Value(BaseModel):
    key: str
    filter: Union[str, None] = None
    expression: Union[str, None] = None
    value: Union[str, None] = None
    sub: Optional[List['Value']] = None

# class ValueList(BaseModel):
#     data: List[Value]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

async def load_data(sub, df_name):
    df = pd.read_excel(f"../data_tables/{sub}/{df_name}.xlsx")
    user_tables[sub] = {user_tables[df_name]: df}
    print(f"Data {sub}/{df_name} loaded into memory")
# def cleanup_expired_users():
#     read_data.remove_expired_users()

# scheduler = BackgroundScheduler()
# scheduler.add_job(cleanup_expired_users, 'interval', seconds=60)
# # scheduler.start()
read_data.flush()

@app.get("/jwk")
def get_jwk():
    return {"keys": [{"e":"AQAB","kty":"RSA","n":"3umIRQ-1weEms044tv5Fzb076bG4wyXx8eTMZJeNzlForlo9WVIO5GYuHpCD8v6viYUwrJGl77eMtBEw3hjRi0T6jCdlJlS-MGk99L2BIAAvXf9AhSHXuiY0clenwhgQHiBBnPrGLcSfNaRtVw1O2Vcvt6c1t7c8jfO7akLj1-zpeavIu4M8YbhF-fAip6DkX09b1npTtTXidYMu739G7Jf4jy0o9Obt13YUC-f7ivPOHK7nYLN50h7k2w0qj-DY_QKdLo8xk9edZzrc7uW6viGJWkMAOx60lrNyhnne_D_6atpN6rqvOYnC4V1Zt4P4mF7ofczGni8o3ckPW32OCQ"}]}


# @app.get("/get_rows")
# async def getR(sub: HeaderParameter):
#     print(sub)
#     return tb.get_rows()

@app.get("/get_table")
async def getT(exp: HeaderParameter, sub: HeaderParameter, n:int=10, pg:int=0, df_name='bills'):
    if not sub in user_tables or not df_name in user_tables[sub]:
        return "Таблица не загружена"
    df = user_tables[sub][df_name]
    if n == 0 and pg == 0:
        data = df.to_dict('records')
        return data
    start_idx = pg * n
    end_idx = start_idx + n
    print(n, pg, start_idx, end_idx)
    data = df.iloc[start_idx:end_idx].to_dict('records')
    return data
    # result = tb.get_table(sub, df_name, n, pg)
    # if len(result) == 0:
    #     return "Загрузите таблицу"
    # return result

@app.get("/pre_load_table")
async def pre_load_T(exp: HeaderParameter, sub: HeaderParameter, df_name='bills'):
    print(sub)
    task = celery_get_table.delay(sub, df_name, 0, 0)
    return {
        "task_id": task.id
    }

@app.post("/filter")
async def filterR(exp: HeaderParameter, sub: HeaderParameter, data: List[Value], n:int=10, pg:int=0, df_name='bills'):
    task = celery_use_filter.delay(jsonable_encoder(data), sub, df_name, n, pg)
    return {
        "task_id": task.id
    }
    # return tb.use_filter(data, sub, df_name, n, pg)

@app.get("/list_files")
async def list_files(exp: HeaderParameter, sub: HeaderParameter, df_name='bills'):

    return mini.list_files('user-tabels',sub,df_name)

@app.get("/get_rows")
async def getR(exp: HeaderParameter, sub: HeaderParameter, df_name='bills'):
    task = celery_get_rows.delay(sub, df_name)
    return {
        "task_id": task.id
    }

@app.post("/load_table")
async def getR(exp: HeaderParameter, sub: HeaderParameter, file: UploadFile, df_name='bills'):
    print(exp, sub)
    read_data.add_user(exp, sub)
    mini.load_data_bytes("user-tabels", f"{sub}/{df_name}/{file.filename}", file.file.read())

@app.delete("/delete_table")
async def delR(exp: HeaderParameter, sub: HeaderParameter, filename, df_name='bills'):
    err = mini.delete_file('user-tabels',sub,df_name,filename)
    return err

@app.post('/add_config', summary='Get history of currently logged in user')
async def add_config(exp: HeaderParameter, sub: HeaderParameter, data = Body()):
    conf = db.add_new_configuration(sub, data)
    return conf

@app.get('/history', summary='Get history of currently logged in user')
async def get_history(exp: HeaderParameter, sub: HeaderParameter):
    conf = db.get_user_configurations(sub)
    if conf == None:
         pass
    return conf

@app.get('/long_task')
async def long_task():
    task = send_email_report_dashboard.delay("Kek")
    return {
        "task_id": task.id
    }

@app.get('/task_status/{task_id}')
async def task_status(task_id: str):
    task = send_email_report_dashboard.AsyncResult(task_id)
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
        # Что-то пошло не так, задача не выполнена
        response = {
            "status": "FAILURE",
            "result": str(task.info),  # task.info содержит исключение, если задача не выполнена
        }
    return response

# @app.get("/get_hardcoded/{user}")
# async def load_hardcoded(user):
#     return mini.list_objects("user-tabels", "12312-asd-12333/hardcoded/")

# @app.get("/get_bills/{user}")
# async def load_hardcoded(user,name, file: UploadFile):
#     return mini.load_data_bytes("user-tabels", f"{user}/bills/{name}.xlsx", file.file.read())

# @app.post("/load_hardcoded/{user}/{name}")
# async def load_hardcoded(user,name, file: UploadFile):
#     mini.load_data_bytes("user-tabels", f"{user}/hardcoded/{name}.xlsx", file.file.read())

# @app.post("/load_bills/{user}/{name}")
# async def load_hardcoded(user,name, file: UploadFile):
#     mini.load_data_bytes("user-tabels", f"{user}/bills/{name}.xlsx", file.file.read())