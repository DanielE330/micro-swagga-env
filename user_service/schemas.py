from pydantic import BaseModel

class UserCreate(BaseModel):
    login: str
    password: str

class UserUpdate(BaseModel):
    login: str | None = None
    password: str | None = None