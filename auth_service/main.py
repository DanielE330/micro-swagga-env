from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session

from database import SessionLocal, engine, Base
import models, schemas, auth

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Auth Service",
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.post("/register")
def register(user: schemas.UserCreate, db: Session = Depends(get_db)) -> dict:
    existing = db.query(models.User).filter_by(login=user.login).first()
    if existing:
        raise HTTPException(status_code=400, detail="пользователь существует")

    new_user = models.User(
        login = user.login,
        password = auth.hash_password(user.password)
    )

    db.add(new_user)
    db.commit()

    return {"message": "пользователь зарегистрирован"}

@app.post("/login")
def login(user: schemas.UserLogin, db: Session = Depends(get_db)) -> dict:
    found_user = db.query(models.User).filter_by(login=user.login).first()

    if not found_user or not auth.verify_password(user.password, found_user.password):
        raise HTTPException(status_code=400, detail="неверный логин или пароль")

    token = auth.create_token({"sub": found_user.login})

    return {"message": "вход выполнен успешно", "token": token}

