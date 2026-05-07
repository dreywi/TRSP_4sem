
from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, EmailStr, conint, constr
from typing import Optional
from sqlalchemy import Column, Integer, String, Float, Text, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import Session
import logging

from app.database import engine, Base, get_db

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

#9.1

class Product(Base):
    __tablename__ = "products"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    price = Column(Float, nullable=False)
    count = Column(Integer, nullable=False, default=0)
    description = Column(Text, nullable=False, default="")  # Добавим во 2й миграции
    created_at = Column(DateTime(timezone=True), server_default=func.now())

# Создаем таблицы
Base.metadata.create_all(bind=engine)


#10.1


class CustomExceptionA(Exception):
    def __init__(self, message: str = "Ошибка бизнес-логики"):
        self.message = message
        self.status_code = 422

class CustomExceptionB(Exception):
    def __init__(self, message: str = "Ресурс не найден"):
        self.message = message
        self.status_code = 404

class ErrorResponse(BaseModel):
    status_code: int
    error_type: str
    message: str
    details: Optional[dict] = None

# Создаем приложение
app = FastAPI(title="Контрольная работа №4")

# Регистрируем обработчики исключений
@app.exception_handler(CustomExceptionA)
async def handle_exc_a(request: Request, exc: CustomExceptionA):
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            status_code=exc.status_code,
            error_type="BusinessError",
            message=exc.message,
            details={"fix": "Проверьте входные данные"}
        ).model_dump()
    )

@app.exception_handler(CustomExceptionB)
async def handle_exc_b(request: Request, exc: CustomExceptionB):
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            status_code=exc.status_code,
            error_type="NotFoundError",
            message=exc.message,
            details={"help": "Проверьте ID ресурса"}
        ).model_dump()
    )


#10.2

class UserRegister(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    age: conint(gt=18, lt=120)
    email: EmailStr
    password: constr(min_length=8, max_length=16)
    phone: Optional[str] = "Unknown"

class RegisterResponse(BaseModel):
    success: bool
    username: str
    email: str
    message: str


# In-memory БД для тестов

memory_db = {}
counter = 0

def get_next_id():
    global counter
    counter += 1
    return counter


#эндпоинты


@app.get("/")
def root():
    return {"message": "Контрольная работа №4", "status": "ok"}

#эндпоинты для 10.1

@app.get("/validate/{value}")
def validate_value(value: int):
    if value < 0:
        raise CustomExceptionA("Значение не может быть отрицательным")
    if value == 0:
        raise CustomExceptionA("Значение не может быть нулем")
    return {"status": "ok", "value": value}

@app.get("/resource/{resource_id}")
def get_resource(resource_id: int):
    resources = {1: "Данные 1", 2: "Данные 2", 3: "Данные 3"}
    if resource_id not in resources:
        raise CustomExceptionB(f"Ресурс {resource_id} не найден")
    return {"status": "ok", "data": resources[resource_id]}

#эндпоинт для 10.2

@app.post("/register", response_model=RegisterResponse, status_code=201)
def register_user(user: UserRegister):
    if user.username.lower() == "admin":
        raise HTTPException(status_code=400, detail="Имя admin занято")
    
    logger.info(f"Регистрация: {user.username}")
    return RegisterResponse(
        success=True,
        username=user.username,
        email=user.email,
        message=f"Пользователь {user.username} зарегистрирован"
    )

#эндпоинты для тестов

@app.post("/users", status_code=201)
def create_user(user: UserRegister):
    user_id = get_next_id()
    memory_db[user_id] = {
        "id": user_id,
        "username": user.username,
        "age": user.age,
        "email": user.email
    }
    return {"id": user_id, "username": user.username, "email": user.email}

@app.get("/users/{user_id}")
def get_user(user_id: int):
    if user_id not in memory_db:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    return memory_db[user_id]

@app.delete("/users/{user_id}", status_code=204)
def delete_user(user_id: int):
    if user_id not in memory_db:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    del memory_db[user_id]
    return None

#эндпоинты для продуктов

@app.get("/products")
def list_products(db: Session = Depends(get_db)):
    products = db.query(Product).all()
    return [{"id": p.id, "title": p.title, "price": p.price, "count": p.count} for p in products]

@app.post("/products", status_code=201)
def create_product(title: str, price: float, count: int, db: Session = Depends(get_db)):
    product = Product(title=title, price=price, count=count)
    db.add(product)
    db.commit()
    db.refresh(product)
    return {"id": product.id, "title": product.title, "price": product.price}