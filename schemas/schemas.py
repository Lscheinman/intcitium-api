# studybuddy/models/schemas.py

from pydantic import BaseModel
from typing import List, Dict

class AnswerRequest(BaseModel):
    question: str
    user_answer: str

class AnswerResponse(BaseModel):
    result: str
    correct_answer: str = None

class ScoreResponse(BaseModel):
    percentage: float
    correct: int
    total: int

class ReportRequest(BaseModel):
    mode: str
    score: float
    missed_words: List[Dict[str, str]]

class RegisterRequest(BaseModel):
    username: str
    password: str