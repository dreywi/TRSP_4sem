from fastapi import FastAPI
from fastapi.responses import FileResponse
from pydantic import BaseModel
from models import Numbers
from models import User
from models import UserAge
from models import Feedback
from models import FeedbackValidated

app = FastAPI()

@app.get("/")
async def root():
    return {"message": "Добро пожаловать в моё приложение FastAPI!"}


@app.get("/")
async def get_html():
    return FileResponse("index.html")



class Numbers(BaseModel):
    num1: float
    num2: float

@app.post("/calculate")
async def calculate(nums: Numbers):
    return {"result": nums.num1 + nums.num2}



user = User(name="Пользователь", id=1)

@app.get("/users")
async def get_user():
    return user

@app.post("/user")
async def check_adult(user: UserAge):
    return {
        "name": user.name,
        "age": user.age,
        "is_adult": user.age >= 18
    }

feedbacks = []

@app.post("/feedback")
async def create_feedback(fb: Feedback):
    feedbacks.append(fb)
    return {"message": f"Feedback received. Thank you, {fb.name}."}

feedbacks_validated = []

@app.post("/feedback")
async def create_feedback_validated(fb: FeedbackValidated):
    feedbacks_validated.append(fb)
    return {"message": f"Спасибо, {fb.name}! Ваш отзыв сохранён."}