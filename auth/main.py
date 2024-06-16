from fastapi import FastAPI, status, HTTPException, Depends, Body, Request
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.responses import RedirectResponse
from utils.schemas import UserOut, UserAuth, TokenSchema, SystemUser
import utils.db_w as db
import json
from fastapi import FastAPI, Header
from typing_extensions import Annotated
from typing import List, Union
from pydantic import BaseModel

HeaderParameter = Annotated[Union[str, None], Header()]

# from replit import db
from utils.utils import (
    get_hashed_password,
    create_access_token,
    create_refresh_token,
    verify_password,
    PUBLIC_KEY
)
from uuid import uuid4
from utils.deps import get_current_user, refresh_current_user

app = FastAPI()

class Token(BaseModel):
    refresh_token: str

@app.get('/', response_class=RedirectResponse, include_in_schema=False)
async def docs():
    return RedirectResponse(url='/docs')

@app.get("/api/jwk")
def get_jwk():
    return {"keys": [json.loads(PUBLIC_KEY)]}

@app.post('/signup', summary="Create new user", response_model=UserOut)
async def create_user(data: UserAuth):
    user = db.get_user(data.username)
    if user is not None:
            raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email already exist"
        )
    user = {
        'username': data.username,
        'password': get_hashed_password(data.password),
        'id': str(uuid4())
    }
    db.add_new_user(username=user['username'], token_password=user['password'])    # saving user to database
    return user


@app.post('/login', summary="Create access and refresh tokens for user", response_model=TokenSchema)
async def login(userr: UserAuth):
    user = db.get_user(userr.username)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect email or password"
        )
    user = user.as_dict()
    hashed_pass = user['token_password']
    if not verify_password(userr.password, hashed_pass):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect email or password"
        )
    
    return {
        "access_token": create_access_token(user['username']),
        "refresh_token": create_refresh_token(user['username']),
    }

@app.get('/me', summary='Get details of currently logged in user', response_model=UserOut)
async def get_me(user: SystemUser = Depends(get_current_user)):
    return user

@app.post('/add_config', summary='Get history of currently logged in user')
async def add_config(user: SystemUser = Depends(get_current_user), data = Body()):
    conf = db.add_new_configuration(user['id'], data)
    return conf

@app.get('/history', summary='Get history of currently logged in user')
async def get_history(user: SystemUser = Depends(get_current_user)):
    conf = db.get_user_configurations(user['id'])
    if conf == None:
         pass
    return conf

@app.post('/refresh', summary="Refresh tokens for user", response_model=TokenSchema)
async def refresh_me(token: Token):
    user = await refresh_current_user(token.refresh_token)
    print(user)
    user = db.get_user(user['username'])
    if user != None:
        user = user.as_dict()
        return {
        "access_token": create_access_token(user['username']),
        "refresh_token": create_refresh_token(user['username']),
    }
    else:
         raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )