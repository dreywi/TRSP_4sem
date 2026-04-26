from fastapi import FastAPI, HTTPException, Response, Request, Cookie, Header, Depends
from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional, Dict
from datetime import datetime
import uuid
import time
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired

app = FastAPI(
    title="🏡 Уютный Дом API 🏡",
    description="Контрольная работа №2"
)

SECRET_KEY = "cozy-home-secret-key-2025"
serializer = URLSafeTimedSerializer(SECRET_KEY)

FAKE_USERS_DB: Dict[str, str] = {
    "diana": "12345",
    "cozy_lover": "home123",
    "user123": "password123"
}

SESSION_DURATION = 300
RENEW_THRESHOLD = 180

#задание 3.1
class UserCreate(BaseModel):
    name: str = Field(..., min_length=1, description="Ваше имя")
    email: EmailStr
    age: Optional[int] = Field(None, ge=0, description="Возраст")
    is_subscribed: Optional[bool] = False

@app.post("/create_user")
async def create_user(user: UserCreate):
    return {
        "message": f"🏠 Добро пожаловать в уютный уголок, {user.name}!",
        "user": user.model_dump()
    }

#задание 3.2
sample_products = [
    {"product_id": 123, "name": "🕯️ Ванильная ароматическая свеча", "category": "Candles", "price": 15.99},
    {"product_id": 456, "name": "🛋️ Мягкий пледик с кисточками", "category": "Textiles", "price": 89.99},
    {"product_id": 789, "name": "☕ Керамическая кружка 'Обниму'", "category": "Kitchenware", "price": 24.99},
    {"product_id": 101, "name": "💡 Солевая лампа 'Гималаи'", "category": "Lighting", "price": 45.99},
    {"product_id": 202, "name": "📖 Деревянная полка для книг", "category": "Furniture", "price": 129.99},
    {"product_id": 303, "name": "🧦 Вязаный плед 'Кашемир'", "category": "Textiles", "price": 149.99},
    {"product_id": 404, "name": "🌸 Аромалампа с эфирными маслами", "category": "Lighting", "price": 34.99},
    {"product_id": 505, "name": "🪴 Фикус в кашпо 'Зелёный друг'", "category": "Plants", "price": 29.99},
    {"product_id": 606, "name": "📚 Настольная лампа для чтения", "category": "Lighting", "price": 59.99},
    {"product_id": 707, "name": "🍵 Заварник 'Вечерний чай'", "category": "Kitchenware", "price": 39.99}
]

@app.get("/product/{product_id}")
async def get_product(product_id: int):
    for product in sample_products:
        if product["product_id"] == product_id:
            return {
                "product": product,
                "message": "🏡 Вот такой уютный товар!"
            }
    raise HTTPException(status_code=404, detail="😢 Товар не найден. Попробуйте другой ID")

@app.get("/products/search")
async def search_products(
    keyword: str,
    category: Optional[str] = None,
    limit: int = 10
):
    results = []
    for product in sample_products:
        if keyword.lower() in product["name"].lower():
            if category is None or product["category"].lower() == category.lower():
                results.append(product)
    
    if not results:
        return {"message": "🔍 Ничего не найдено... Попробуйте: свеча, плед, кружка, лампа", "products": []}
    
    return {
        "message": f"🏠 Найдено {min(len(results), limit)} уютных товаров",
        "products": results[:limit]
    }

#задание 5.1 5.2 5.3
class LoginData(BaseModel):
    username: str
    password: str

def create_signed_session(user_id: str, username: str) -> str:
    payload = {"user_id": user_id, "username": username}
    return serializer.dumps(payload)

@app.post("/login")
async def login(response: Response, login_data: LoginData):
    if login_data.username not in FAKE_USERS_DB or FAKE_USERS_DB[login_data.username] != login_data.password:
        raise HTTPException(status_code=401, detail="❌ Неверный логин или пароль")
    
    user_id = str(uuid.uuid4())
    session_token = create_signed_session(user_id, login_data.username)
    
    response.set_cookie(
        key="session_token",
        value=session_token,
        httponly=True,
        max_age=SESSION_DURATION,
        secure=False
    )
    return {"message": f"🏡 Добро пожаловать домой, {login_data.username}!"}

@app.get("/profile")
async def get_profile(response: Response, request: Request, session_token: Optional[str] = Cookie(None)):
    if not session_token:
        raise HTTPException(status_code=401, detail="🔒 Пожалуйста, войдите в систему через POST /login")
    
    try:
        data = serializer.loads(session_token, max_age=SESSION_DURATION)
        inner_data, timestamp = serializer.loads_unsafe(session_token, max_age=None)
        age = time.time() - timestamp
        
        #обновляем сессию, если прошло 3-5 минут
        if age >= RENEW_THRESHOLD and age < SESSION_DURATION:
            new_token = create_signed_session(data["user_id"], data["username"])
            response.set_cookie(
                key="session_token",
                value=new_token,
                httponly=True,
                max_age=SESSION_DURATION,
                secure=False
            )
            renewed_flag = True
            renewal_message = "🔄 Сессия продлена! Ваш уютный уголок ждёт вас ещё 5 минут"
        else:
            renewed_flag = False
            renewal_message = "✨ Сессия активна, уют сохраняется"
        
        return {
            "message": f"🕯️ Привет, {data['username']}! Твой уютный уголок ждёт тебя",
            "user_id": data["user_id"],
            "session_status": renewal_message,
            "session_age_seconds": round(age, 2),
            "renewed": renewed_flag
        }
    
    except SignatureExpired:
        raise HTTPException(status_code=401, detail="⏰ Сессия истекла. Зайдите снова через /login")
    except BadSignature:
        raise HTTPException(status_code=401, detail="🔐 Недействительная сессия. Данные были изменены!")

# Задание 5.4: Заголовки
class CommonHeaders(BaseModel):
    user_agent: str = Field(..., alias="User-Agent")
    accept_language: str = Field(..., alias="Accept-Language")
    
    @field_validator("accept_language")
    @classmethod
    def validate_accept_language(cls, v: str) -> str:
        if not v or not isinstance(v, str):
            raise ValueError("Accept-Language должен быть строкой")
        return v
    
    class Config:
        populate_by_name = True

@app.get("/headers")
async def get_headers_endpoint(headers: CommonHeaders = Depends()):
    return {
        "message": "📋 Твои заголовки запроса:",
        "headers": headers.model_dump(by_alias=True)
    }

@app.get("/info")
async def info_endpoint(response: Response, headers: CommonHeaders = Depends()):
    current_time = datetime.utcnow().isoformat()
    response.headers["X-Server-Time"] = current_time
    
    return {
        "message": "🏡 Добро пожаловать в уютный API! Ваши заголовки успешно обработаны. Создавайте уют вместе с нами 🕯️📚",
        "headers": headers.model_dump(by_alias=True)
    }

#корневой маршрут
@app.get("/")
async def root():
    return {
        "message": "🏡 Добро пожаловать в API 'Уютный Дом'! 🕯️📚☕",
        "endpoints": {
            "📦 Создать пользователя": "POST /create_user",
            "🕯️ Товар по ID": "GET /product/123",
            "🔎 Поиск уютных товаров": "GET /products/search?keyword=плед",
            "🔑 Войти": "POST /login (diana / 12345)",
            "👤 Мой профиль": "GET /profile",
            "📋 Заголовки": "GET /headers",
            "ℹ️ Инфо с заголовками": "GET /info"
        },
        "категории_товаров": ["Candles (свечи)", "Textiles (пледы)", "Kitchenware (посуда)", "Lighting (свет)", "Furniture (мебель)", "Plants (растения)"] 
    }