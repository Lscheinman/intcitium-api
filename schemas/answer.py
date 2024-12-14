# schemas/answer.py
from pydantic import BaseModel

class AnswerRequest(BaseModel):
    question: str
    user_answer: str

class AnswerResponse(BaseModel):
    result: str
    correct_answer: str = None
