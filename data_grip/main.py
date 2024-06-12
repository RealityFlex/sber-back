# from __future__ import annotations
import uvicorn
from fastapi import FastAPI, File, UploadFile, status, Header, Request, Depends, BackgroundTasks, Body
from apscheduler.schedulers.background import BackgroundScheduler
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from tables import Table
from pydantic import BaseModel
from typing import Union, List, Optional, Annotated
import mini
import json
import read_data
import db_w as db
HeaderParameter = Annotated[Union[str, None], Header()]
app = FastAPI()

tb = Table("low_data.xlsx")

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

def cleanup_expired_users():
    read_data.remove_expired_users()

scheduler = BackgroundScheduler()
scheduler.add_job(cleanup_expired_users, 'interval', seconds=60)
scheduler.start()

@app.on_event("shutdown")
def shutdown_event():
    scheduler.shutdown()

@app.get("/jwk")
def get_jwk():
    return {"keys": [{"e":"AQAB","kty":"RSA","n":"3umIRQ-1weEms044tv5Fzb076bG4wyXx8eTMZJeNzlForlo9WVIO5GYuHpCD8v6viYUwrJGl77eMtBEw3hjRi0T6jCdlJlS-MGk99L2BIAAvXf9AhSHXuiY0clenwhgQHiBBnPrGLcSfNaRtVw1O2Vcvt6c1t7c8jfO7akLj1-zpeavIu4M8YbhF-fAip6DkX09b1npTtTXidYMu739G7Jf4jy0o9Obt13YUC-f7ivPOHK7nYLN50h7k2w0qj-DY_QKdLo8xk9edZzrc7uW6viGJWkMAOx60lrNyhnne_D_6atpN6rqvOYnC4V1Zt4P4mF7ofczGni8o3ckPW32OCQ"}]}

# @app.get("/get_rows")
# async def getR(sub: HeaderParameter):
#     print(sub)
#     return tb.get_rows()

@app.get("/get_table")
async def getT(exp: HeaderParameter, sub: HeaderParameter, df_name, n:int=10, pg:int=0):
    print(sub)
    read_data.add_user(exp, sub)
    return tb.get_table(sub, df_name, n, pg)

@app.post("/filter")
async def filterR(exp: HeaderParameter, sub: HeaderParameter, df_name, data: List[Value], n:int=10, pg:int=0):
     read_data.add_user(exp, sub)
     return tb.use_filter(data, sub, df_name, n, pg)

@app.get("/list_files")
async def list_files(exp: HeaderParameter, sub: HeaderParameter, df_name):
    read_data.add_user(exp, sub)
    return mini.list_files('user-tabels',sub,df_name)

@app.get("/get_rows")
async def getR(exp: HeaderParameter, sub: HeaderParameter, df_name):
    print(exp, sub)
    read_data.add_user(exp, sub)
    return tb.get_rows(sub, df_name)

@app.post("/load_table")
async def getR(exp: HeaderParameter, sub: HeaderParameter, df_name, file: UploadFile):
    print(exp, sub)
    read_data.add_user(exp, sub)
    mini.load_data_bytes("user-tabels", f"{sub}/{df_name}/{file.filename}", file.file.read())

@app.delete("/delete_table")
async def delR(exp: HeaderParameter, sub: HeaderParameter, df_name, filename):
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