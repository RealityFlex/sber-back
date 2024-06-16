import uvicorn
from fastapi import FastAPI, File, UploadFile, status, Header, Request, Depends, BackgroundTasks, Body, HTTPException
from apscheduler.schedulers.background import BackgroundScheduler
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.encoders import jsonable_encoder
from utils.tables_fast import Table
from pydantic import BaseModel
from typing import Union, List, Optional, Annotated, Dict, Any
# import mini
import json
import utils.read_data_fast as read_data
import asyncio
import utils.db_w as db
import uuid
import pandas as pd
from tasks import celery_use_filter, celery_get_rows, celery_get_table, get_res
HeaderParameter = Annotated[Union[str, None], Header()]
app = FastAPI()

origins = [
    "*",
]

tb = Table()
# tb.init()

@app.get("/api/jwk")
def get_jwk():
    return {"keys": [{"e":"AQAB","kty":"RSA","n":"3umIRQ-1weEms044tv5Fzb076bG4wyXx8eTMZJeNzlForlo9WVIO5GYuHpCD8v6viYUwrJGl77eMtBEw3hjRi0T6jCdlJlS-MGk99L2BIAAvXf9AhSHXuiY0clenwhgQHiBBnPrGLcSfNaRtVw1O2Vcvt6c1t7c8jfO7akLj1-zpeavIu4M8YbhF-fAip6DkX09b1npTtTXidYMu739G7Jf4jy0o9Obt13YUC-f7ivPOHK7nYLN50h7k2w0qj-DY_QKdLo8xk9edZzrc7uW6viGJWkMAOx60lrNyhnne_D_6atpN6rqvOYnC4V1Zt4P4mF7ofczGni8o3ckPW32OCQ"}]}

class Operation(BaseModel):
    value: Optional[str] = None
    filter: Optional[str] = None
    expression: Optional[str] = None
    sub: Optional[List['Configuration']] = None

class Configuration(BaseModel):
    column: str
    operations: List[Operation]

class FilterData(BaseModel):
    configurations: List[Configuration]

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

@app.get("/api/tables/get_table", summary="Получить данные таблицы", tags=["Получение данных"])
async def getT(
    exp: str = Header(..., description="Параметр заголовка exp"),
    sub: str = Header(..., description="Параметр заголовка sub"),
    n: int = 10,
    pg: int = 0,
    df_name: str = 'bills'
):
    """
    Получить данные таблицы для конкретного пользователя.

    - **exp**: Параметр заголовка exp.
    - **sub**: Параметр заголовка sub.
    - **n**: Количество записей на странице (по умолчанию 10).
    - **pg**: Номер страницы (по умолчанию 0).
    - **df_name**: Название таблицы (по умолчанию 'bills').

    Возвращает:
    - Весь набор данных, если n и pg равны 0.
    - Сообщение "Таблица не загружена", если таблица не найдена.
    - Страницу данных с n записями.
    """
    read_data.add_user(exp, sub)
    df_name = df_name+"_edit"
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
                    "rows": total_rows,
                    "pages": total_pages
                },
                "data": data}

@app.post("/api/tables/sort", response_model=Union[List[dict], str], summary="Сортировка и фильтрация данных таблицы", tags=["Изменение таблиц"])
async def sortT(
    sort: Sort = Body(..., description="Параметры сортировки и фильтрации"),
    exp: Optional[str] = Header(None, description="Параметр заголовка exp"),
    sub: Optional[str] = Header(None, description="Параметр заголовка sub"),
    n: int = 10,
    pg: int = 0,
    df_name: str = 'bills'
    ):
    """
    Сортировка и фильтрация данных таблицы для конкретного пользователя.

    - **sort**: Объект, содержащий параметры сортировки и фильтрации.
    - **exp**: Параметр заголовка exp.
    - **sub**: Параметр заголовка sub.
    - **n**: Количество записей на странице (по умолчанию 10).
    - **pg**: Номер страницы (по умолчанию 0).
    - **df_name**: Название таблицы (по умолчанию 'bills').

    Возвращает:
    - Отсортированные и/или отфильтрованные данные с пагинацией.
    - Сообщение "Таблица не загружена", если таблица не найдена.
    """
    df_name = df_name+"_edit"

    read_data.add_user(exp, sub)
    df = read_data.get_df(sub, df_name)
    if df.empty:
        raise HTTPException(status_code=404, detail="Таблица не загружена")
    
    df = df.sort_values(by=sort.keys, ascending=sort.ascending)
    
    if sort.find:
        # Преобразуем указанные колонки в строковый тип для поиска
        df_cp = df[sort.keys].astype(str)
        # Формируем маску для поиска
        mask = df_cp.apply(lambda row: row.str.contains(sort.find, na=False).any(), axis=1)
        # Фильтруем DataFrame по маске
        df = df[mask]
    
    start_idx = pg * n
    end_idx = start_idx + n
    data = df.iloc[start_idx:end_idx].to_dict('records')
    
    read_data.set_df(sub, df_name, df)
    return data

@app.get("/api/tables/restore", summary="Откатить изменения таблицы", tags=["Изменение таблиц"])
async def restore(
    exp: Optional[str] = Header(None, description="Параметр заголовка exp"),
    sub: Optional[str] = Header(None, description="Параметр заголовка sub"),
    n: int = 10,
    pg: int = 0,
    df_name: str = 'bills'
):
    await tb.restore_table(sub, df_name)

@app.post("/api/tables/edit_cell", response_model=Union[List[dict], str], summary="Редактирование ячеек таблицы", tags=["Изменение таблиц"])
async def edit_C(
    edit: Edit = Body(..., description="Параметры редактирования ячеек"),
    exp: Optional[str] = Header(None, description="Параметр заголовка exp"),
    sub: Optional[str] = Header(None, description="Параметр заголовка sub"),
    n: int = 10,
    pg: int = 0,
    df_name: str = 'bills'
):
    """
    Редактирование ячеек таблицы для конкретного пользователя.

    - **edit**: Объект, содержащий параметры редактирования.
    - **exp**: Параметр заголовка exp.
    - **sub**: Параметр заголовка sub.
    - **n**: Количество записей на странице (по умолчанию 10).
    - **pg**: Номер страницы (по умолчанию 0).
    - **df_name**: Название таблицы (по умолчанию 'bills').

    Возвращает:
    - Обновленные данные с пагинацией.
    - Сообщение "Таблица не загружена", если таблица не найдена.
    - Сообщение об ошибке при редактировании.
    """
    read_data.add_user(exp, sub)
    df_name = df_name + "_edit"
    df = read_data.get_df(sub, df_name)
    
    if df.empty:
        raise HTTPException(status_code=404, detail="Таблица не загружена")
    
    try:
        # Получаем индексы строк и столбцов
        row_idx = edit.row
        col_idx = edit.column
        
        if edit.value == 'del' and edit.column is None:
            # Удаляем строки
            df = df.drop(row_idx).reset_index(drop=True)
        else:
            # Изменяем значения в указанных строках и столбцах
            for i in row_idx:
                dtype = df[col_idx].dtype  # Получаем тип данных столбца
                df.at[i, col_idx] = dtype.type(edit.value)
                
    except Exception as e:
        return f"Error editing DataFrame: {e}"
    
    start_idx = pg * n
    end_idx = start_idx + n
    data = df.iloc[start_idx:end_idx].to_dict('records')
    
    read_data.set_df(sub, df_name, df)
    return data

@app.get("/api/tables/pre_load_table", summary="Предварительная загрузка данных таблицы", tags=["Работа с файлами таблиц"])
async def getT(
    exp: Optional[str] = Header(None, description="Параметр заголовка exp"),
    sub: Optional[str] = Header(None, description="Параметр заголовка sub"),
    n: int = 10,
    pg: int = 0,
    df_name: str = 'bills'
    ):
    """
    Предварительная загрузка данных таблицы для конкретного пользователя.

    - **exp**: Параметр заголовка exp.
    - **sub**: Параметр заголовка sub.
    - **n**: Количество записей на странице (по умолчанию 10).
    - **pg**: Номер страницы (по умолчанию 0).
    - **df_name**: Название таблицы (по умолчанию 'bills').

    Возвращает:
    - Сообщение о начале загрузки данных.
    """
    try:
        read_data.add_user(exp, sub)
        asyncio.create_task(read_data.load_df(sub, df_name))
        return {"message": "Загрузка данных началась"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка при запуске загрузки данных: {e}")

@app.get("/api/tables/list_files", summary="Получение списка файлов", tags=["Получение данных"])
async def list_files(
    exp: str = Header(None, description="Параметр заголовка exp"),
    sub: str = Header(None, description="Параметр заголовка sub"),
    df_name: str = 'bills'
):
    """
    Получение списка файлов для указанного пользователя и названия таблицы.

    - **exp**: Параметр заголовка exp.
    - **sub**: Параметр заголовка sub.
    - **df_name**: Название таблицы (по умолчанию 'bills').

    Возвращает:
    - Список названий колонок таблицы.
    - HTTP исключение с кодом 404, если таблица не загружена или не найдена.
    """
    try:
        read_data.add_user(exp, sub)
        return await read_data.get_list_files(sub, df_name)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка при получении списка файлов: {e}")

@app.post("/api/tables/filter", summary="Фильтрация данных в таблице", tags=["Изменение таблиц"])
async def filterR(
    exp: str = Header(None, description="Параметр заголовка exp"),
    sub: str = Header(None, description="Параметр заголовка sub"),
    data: FilterData = Body(..., description="Список значений для фильтрации"),
    df_name: str = 'bills_edit'
    ):
    """
    Фильтрация данных в указанной таблице для конкретного пользователя.

    - **exp**: Параметр заголовка exp.
    - **sub**: Параметр заголовка sub.
    - **data**: Список значений для фильтрации.
    - **df_name**: Название таблицы (по умолчанию 'bills_edit').

    Возвращает:
    - Сообщение о запуске задачи фильтрации и идентификатор задачи.
    """
    try:
        read_data.add_user(exp, sub)
        task_id = str(uuid.uuid4())
        tasks[task_id] = {"status": "in_progress", "result": None}

        async def task_wrapper():
            try:
                # Преобразование данных перед фильтрацией
                filter_data = [conf.dict() for conf in data.configurations]
                result = await tb.use_filter(data=filter_data, sub=sub, df_name="filter", df_real=read_data.get_df(sub, df_name))
                tasks[task_id]["status"] = "completed"
                tasks[task_id]["result"] = result
            except Exception as e:
                tasks[task_id]["status"] = "failed"
                tasks[task_id]["result"] = str(e)
        
        read_data.set_df(sub, 'config', data.dict())
        asyncio.create_task(task_wrapper())

        return {"message": "Задача улетела", 'id': task_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка при фильтрации данных: {e}")

@app.get("/api/tables/status/{task_id}", summary="Получение статуса задачи", tags=["Проверка статуса операций"])
async def get_status(task_id: str):
    """
    Получение текущего статуса задачи по её идентификатору.

    - **task_id**: Идентификатор задачи.

    Возвращает:
    - Состояние задачи (in_progress, completed, failed).
    - HTTP исключение с кодом 404, если задача не найдена.
    """
    if task_id not in tasks:
        raise HTTPException(status_code=404, detail="Задача не найдена")
    
    return tasks[task_id]

@app.post("/api/tables/load_table", summary="Загрузка таблицы", tags=["Работа с файлами таблиц"])
async def loadT(
    exp: str = Header(None, description="Параметр заголовка exp"),
    sub: str = Header(None, description="Параметр заголовка sub"),
    df_name: str = 'bills',
    file: UploadFile = None
):
    """
    Загрузка файла данных в указанную таблицу для конкретного пользователя.

    - **exp**: Параметр заголовка exp.
    - **sub**: Параметр заголовка sub.
    - **file**: Загружаемый файл.
    - **df_name**: Название таблицы (по умолчанию 'bills').

    Возвращает:
    - Сообщение о начале загрузки данных.
    """
    try:
        read_data.add_user(exp, sub)
        filename = file.filename
        file_content = await file.read()
        asyncio.create_task(read_data.upload_tb_df(sub, df_name, f"{sub}/{df_name}/{filename}", file_content))
        
        return {"message": "Загрузка данных началась"}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка при загрузке таблицы: {e}")

@app.delete("/api/tables/delete_table", summary="Удаление таблицы", tags=["Работа с файлами таблиц"])
async def delT(
    exp: str = Header(None, description="Параметр заголовка exp"),
    sub: str = Header(None, description="Параметр заголовка sub"),
    df_name: str = 'bills',
    filename: str = "" 
):
    """
    Удаление таблицы данных для указанного пользователя.

    - **exp**: Параметр заголовка exp.
    - **sub**: Параметр заголовка sub.
    - **filename**: Имя файла таблицы для удаления.
    - **df_name**: Название таблицы (по умолчанию 'bills').

    Возвращает:
    - Сообщение о начале удаления таблицы.
    """
    try:
        read_data.add_user(exp, sub)
        asyncio.create_task(read_data.delete_tb_df(sub, df_name, filename))
        
        return {"message": f"Удаление таблицы '{df_name}' с именем файла '{filename}' началось"}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка при удалении таблицы: {e}")

@app.post('/api/tables/add_config', summary='Добавление конфигурации', tags=["Получение данных"])
async def add_config(
    exp: str = Header(None, description="Параметр заголовка exp"),
    sub: str = Header(None, description="Параметр заголовка sub"),
    data: FilterData = Body(..., description="Список значений для фильтрации")
):
    """
    Добавление новой конфигурации для указанного пользователя.

    - **exp**: Параметр заголовка exp.
    - **sub**: Параметр заголовка sub.
    - **data**: Данные конфигурации.

    Возвращает:
    - Результат операции добавления конфигурации.
    """
    try:
        read_data.add_user(exp, sub)
        conf_json = data.dict()
        conf = db.add_new_configuration(sub, conf_json)
        return conf
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка при добавлении конфигурации: {e}")

@app.get('/api/tables/history', summary='Получение истории конфигураций текущего пользователя', tags=["Получение данных"])
async def get_history(
    exp: str = Header(None, description="Параметр заголовка exp"),
    sub: str = Header(None, description="Параметр заголовка sub")
):
    """
    Получение истории конфигураций текущего пользователя.

    - **exp**: Параметр заголовка exp.
    - **sub**: Параметр заголовка sub.

    Возвращает:
    - Историю конфигураций пользователя или пустой список, если данных нет.
    """
    try:
        read_data.add_user(exp, sub)
        conf = db.get_user_configurations(sub)
        
        if conf is None:
            return {"message": "Конфигурации не найдены"}
        return conf
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка при получении истории конфигураций: {e}")

@app.get('/api/distribution/start')
async def start_distribution( 
    exp: str = Header(None, description="Параметр заголовка exp"),
    sub: str = Header(None, description="Параметр заголовка sub")
    ):
    conf = read_data.get_conf(sub, "config")
    try:
        read_data.add_user(exp, sub)
        conf = db.add_new_configuration(sub, conf)
        return conf
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка при добавлении конфигурации: {e}")

@app.get('/api/distribution/{config_id}', summary='Получение конфигурации пользователя по ID', tags=["Получение данных"])
async def get_distribution(
    exp: str = Header(None, description="Параметр заголовка exp"),
    sub: str = Header(None, description="Параметр заголовка sub"),
    config_id: str = None
    ):
    """
    Получение конфигурации пользователя по указанному ID.

    - **exp**: Параметр заголовка exp.
    - **sub**: Параметр заголовка sub.
    - **config_id**: ID конфигурации пользователя.

    Возвращает:
    - Конфигурацию пользователя или сообщение о её отсутствии.
    """
    try:
        read_data.add_user(exp, sub)
        conf = db.get_user_configuration(config_id)
        
        if conf is None:
            return {"message": "Конфигурация не найдена"}
        
        return conf
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка при получении конфигурации: {e}")

@app.post("/api/distribution/result")
def distribution_result():
    pass

@app.get('/api/tables/task_status/{task_id}', summary='Получение статуса операции Celery по ID', tags=["Проверка статуса операций"])
async def task_status(task_id: str):
    """
    Получение текущего статуса операции по заданному task_id.

    Args:
    - task_id (str): Идентификатор задачи для получения статуса.

    Returns:
    - dict: Словарь с текущим состоянием задачи и её результатом (если есть).
      Примеры:
        - Если задача находится в состоянии 'PENDING':
          {"status": "PENDING", "result": None}
        - Если задача выполнена успешно или находится в процессе выполнения:
          {"status": "SUCCESS", "result": {"sub": "user123", "df_name": "bills"}}
        - Если задача завершилась с ошибкой:
          {"status": "FAILURE", "result": "Информация об ошибке"}

    Raises:
    - HTTPException: Если произошла ошибка при получении статуса задачи.

    """
    try:
        task = await get_res(task_id)
        
        if task["state"] == 'PENDING':
            response = {
                "status": "PENDING",
                "result": None
            }
        elif task["state"] != 'FAILURE':
            res = task["result"]
            if "sub" in res and "df_name" in res:
                asyncio.create_task(load_data(res['sub'], res['df_name']))
            response = {
                "status": task["state"],
                "result": task["result"]
            }
        else:
            response = {
                "status": "FAILURE",
                "result": str(task["info"])  # task["info"] содержит информацию об ошибке
            }
        
        return response
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка при получении статуса задачи: {str(e)}")