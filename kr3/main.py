from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from pydantic import BaseModel
from typing import Dict, Optional
import secrets
from passlib.context import CryptContext
import os
from dotenv import load_dotenv

load_dotenv()


MODE = os.getenv("MODE", "DEV")  
DOCS_USER = os.getenv("DOCS_USER", "admin")
DOCS_PASSWORD = os.getenv("DOCS_PASSWORD", "admin123")

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

#фейковая база пользователей
fake_users_db: Dict[str, dict] = {}

# HTTP Basic Auth
security = HTTPBasic()

class UserBase(BaseModel):
    username: str

class User(UserBase):
    password: str

class UserInDB(UserBase):
    hashed_password: str

def hash_password(password: str) -> str:
    """Хеширование пароля с помощью bcrypt"""
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Проверка пароля"""
    return pwd_context.verify(plain_password, hashed_password)

def get_user_by_username(username: str) -> Optional[UserInDB]:
    """Найти пользователя в фейковой БД"""
    if username in fake_users_db:
        user_data = fake_users_db[username]
        return UserInDB(**user_data)
    return None

def authenticate_user(credentials: HTTPBasicCredentials = Depends(security)) -> UserInDB:
    """
    Зависимость аутентификации (задания 6.1 и 6.2)
    """
    # Защита от тайминг-атак через secrets.compare_digest
    correct_username = secrets.compare_digest(credentials.username, "testuser")
    
    user = get_user_by_username(credentials.username)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Basic"},
        )
    
    if not verify_password(credentials.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Basic"},
        )
    
    return user


def verify_docs_auth(credentials: HTTPBasicCredentials = Depends(security)):
    """Проверка аутентификации для доступа к /docs в режиме DEV"""
    if MODE == "PROD":
        raise HTTPException(status_code=404, detail="Not Found")
    
    #проверяем учетные данные для документации
    correct_user = secrets.compare_digest(credentials.username, DOCS_USER)
    correct_pass = secrets.compare_digest(credentials.password, DOCS_PASSWORD)
    
    if not (correct_user and correct_pass):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials for docs",
            headers={"WWW-Authenticate": "Basic"},
        )
    return True



if MODE == "PROD":
    app = FastAPI(
        title="Контрольная работа №3",
        description="API для управления пользователями",
        docs_url=None,      # отключаем /docs
        redoc_url=None,     # отключаем /redoc
        openapi_url=None    # отключаем /openapi.json
    )
else:
    app = FastAPI(
        title="Контрольная работа №3",
        description="API для управления пользователями",
        docs_url=None,      # отключаем стандартный /docs
        redoc_url=None,     # отключаем стандартный /redoc
        openai_url="/openapi.json"  # оставляем схему, но защитим ее
    )

    from fastapi.openapi.docs import get_swagger_ui_html, get_redoc_html
    
    @app.get("/docs", include_in_schema=False)
    async def get_docs(auth: bool = Depends(verify_docs_auth)):
        return get_swagger_ui_html(openapi_url="/openapi.json", title="API Docs")
    
    @app.get("/redoc", include_in_schema=False)
    async def get_redoc(auth: bool = Depends(verify_docs_auth)):
        return get_redoc_html(openapi_url="/openapi.json", title="ReDoc")
    
    @app.get("/openapi.json", include_in_schema=False)
    async def get_openapi(auth: bool = Depends(verify_docs_auth)):
        return app.openapi()

#эндпоинты (задания 6.1 и 6.2)


@app.post("/register", status_code=status.HTTP_201_CREATED)
async def register_user(user: User):
    """Регистрация нового пользователя с хешированием пароля"""
    if user.username in fake_users_db:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )
    
    hashed = hash_password(user.password)
    fake_users_db[user.username] = {
        "username": user.username,
        "hashed_password": hashed
    }
    
    return {"message": f"User {user.username} created successfully"}

@app.get("/login")
async def login(user: UserInDB = Depends(authenticate_user)):
    """Аутентификация пользователя (задания 6.1 и 6.2)"""
    return {"message": f"You got my secret, welcome {user.username}"}

#тестовый эндпоинт для проверки
@app.get("/")
async def root():
    return {
        "message": "Контрольная работа №3",
        "mode": MODE,
        "docs_available": MODE == "DEV",
        "endpoints": ["/register (POST)", "/login (GET with Basic Auth)"]
    }