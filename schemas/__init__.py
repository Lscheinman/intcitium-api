# schemas/__init__.py
from .answer import AnswerRequest, AnswerResponse
from .report import ReportRequest, ScoreResponse
from .user import RegisterRequest

__all__ = ["AnswerRequest", "AnswerResponse", "ReportRequest", "ScoreResponse", "RegisterRequest"]
