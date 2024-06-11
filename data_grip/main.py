# from __future__ import annotations
import uvicorn
from fastapi import FastAPI, File, UploadFile, status, Header, Request, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from tables import Table
from pydantic import BaseModel
from typing import Union, List, Optional

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

@app.get("/get_rows")
async def getR():
    return tb.get_rows()

@app.get("/get_table")
async def getT(n:int=10, pg:int=0):
    return tb.get_table(n, pg)

@app.post("/filter")
async def filterR(data: List[Value]):
    return tb.use_filter(data)