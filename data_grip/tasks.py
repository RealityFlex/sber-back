import smtplib
from email.message import EmailMessage
import time
from celery import Celery
from celery.result import AsyncResult
from tables_fast import Table
import read_data
import json

tb = Table()

SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 465

celery = Celery('tasks', broker='redis://62.109.8.64:6377', backend='redis://62.109.8.64:6377')
celery.conf.broker_connection_retry_on_startup = True


async def get_res(id):
    return AsyncResult(id, app=celery)

@celery.task
def celery_use_filter(data, sub, df_name, n, pg, df):
    res = tb.use_filter(data, sub, df_name, n, pg, df)
    return {"sub":sub, "df_name":df_name, "result":res}

@celery.task
def celery_get_rows(sub, df_name):
    res = tb.get_rows(sub, df_name)
    return {"sub":sub, "df_name":df_name, "result":res}

@celery.task
def celery_get_table(sub, df_name, n, pg):
    res = tb.get_table(sub, df_name, 0, 0)
    return {"sub":sub, "df_name":df_name, "result":res}