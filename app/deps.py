from typing import Union, Any
from datetime import datetime
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from .utils import (
    ALGORITHM,
    JWT_SECRET_KEY,
    JWT_REFRESH_SECRET_KEY
)

from jose import jwt
from pydantic import ValidationError
from app.schemas import TokenPayload, SystemUser
# from replit import db

reuseable_oauth = OAuth2PasswordBearer(
    tokenUrl="/login",
    scheme_name="JWT"
)

async def refresh_current_user(token: str = Depends(reuseable_oauth)):
    try:
        payload = jwt.decode(
            token, JWT_REFRESH_SECRET_KEY, algorithms=[ALGORITHM]
        )
        return {"email":payload['sub']}
    except(jwt.JWTError, ValidationError):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

async def get_current_user(token: str = Depends(reuseable_oauth)) -> SystemUser:
    try:
        payload = jwt.decode(
            token, JWT_SECRET_KEY, algorithms=[ALGORITHM]
        )
        token_data = TokenPayload(**payload)
        
        if datetime.fromtimestamp(token_data.exp) < datetime.now():
            raise HTTPException(
                status_code = status.HTTP_401_UNAUTHORIZED,
                detail="Token expired",
                headers={"WWW-Authenticate": "Bearer"},
            )
    except(jwt.JWTError, ValidationError):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    user: Union[dict[str, Any], None] = "db.get(token_data.sub, None)"
    
    
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Could not find user",
        )
    
    return {'email': 'Shureck@gmail.com', 'password': '$2b$12$I7ZzCkAcx1LJJ3syBUvyueDeGFcIks2HPpkPeIJDRwBq7nf7BhGca', 'id': 'a80a1f50-7e05-4170-8b6e-4251a6bd677c'}