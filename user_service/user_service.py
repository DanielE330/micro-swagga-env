import os
from datetime import datetime, timedelta
from jose import jwt, JWTError
from fastapi import HTTPException
from passlib.context import CryptContext

def verify_token(token: str) -> str:
    try:
        payload = jwt.decode(token, os.getenv("SECRET_KEY"), algorithms=[os.getenv("ALGORITHM")])
        return payload.get("sub")
    except JWTError:
        raise HTTPException(status_code=401, detail="неверный токен")

def get_current_user(token: str) -> str:
    return verify_token(token)