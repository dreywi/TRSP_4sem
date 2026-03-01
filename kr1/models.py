from pydantic import BaseModel
from pydantic import BaseModel, Field, field_validator
import re

class User(BaseModel):
    name: str
    id: int

class UserAge(BaseModel):
    name: str
    age: int

class Feedback(BaseModel):
    name: str
    message: str


class FeedbackValidated(BaseModel):
    name: str = Field(..., min_length=2, max_length=50)
    message: str = Field(..., min_length=10, max_length=500)

    @field_validator("message")
    @classmethod
    def check_bad_words(cls, v: str):
        bad_words = ["кринж", "рофл", "вайб"]
        pattern = r"\b(" + "|".join(bad_words) + r")\b"
        if re.search(pattern, v.lower()):
            raise ValueError("Использование недопустимых слов")
        return v