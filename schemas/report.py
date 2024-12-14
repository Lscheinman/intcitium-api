# schemas/report.py
from pydantic import BaseModel
from typing import List, Dict, Optional

class ReportRequest(BaseModel):
    mode: str
    score: float
    missed_words: List[Dict[str, str]]

class IncorrectAnswer(BaseModel):
    question: str
    user_answer: str
    correct_answer: str

class ScoreResponse(BaseModel):
    quiz_name: str
    started_on: Optional[str]  # ISO format string
    completed_on: Optional[str]  # ISO format string
    score: Optional[float]
    total_correct: int
    total_incorrect: int
    incorrect_answers: List[IncorrectAnswer]
