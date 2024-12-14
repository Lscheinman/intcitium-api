from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models import Report, Quiz
from schemas import ScoreResponse
from typing import List
from dependencies import get_current_user

router = APIRouter()

@router.get("/by-user", response_model=List[ScoreResponse])
def get_reports_by_user(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Get all reports for the current user.
    """
    reports = Report.get_reports_by_user(db, user_id=current_user.id)
    return [
        {
            "quiz_name": db.query(Quiz).filter(Quiz.id == report.quiz_id).first().name,
            "started_on": report.started_on,
            "completed_on": report.completed_on,
            "score": report.score,
            "total_correct": report.total_correct,
            "total_incorrect": report.total_incorrect,
            "incorrect_answers": report.incorrect_answers,
        }
        for report in reports
    ]

@router.get("/by-quiz/{quiz_id}", response_model=List[ScoreResponse])
def get_reports_by_quiz(quiz_id: int, db: Session = Depends(get_db)):
    """
    Get all reports for a specific quiz.
    """
    # Fetch all reports for the quiz
    reports = Report.get_reports_by_quiz(db, quiz_id=quiz_id)
    if not reports:
        raise HTTPException(status_code=404, detail="No reports found for this quiz")

    # Get the quiz name
    quiz = db.query(Quiz).filter(Quiz.id == quiz_id).first()
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found")

    # Transform the reports into the expected schema format
    return [
        {
            "quiz_name": quiz.name,
            "started_on": report.started_on.isoformat() if report.started_on else None,
            "completed_on": report.completed_on.isoformat() if report.completed_on else None,
            "score": report.score,
            "total_correct": report.total_correct,
            "total_incorrect": report.total_incorrect,
            "incorrect_answers": report.incorrect_answers if report.incorrect_answers else [],
        }
        for report in reports
    ]

@router.get("/{report_id}", response_model=ScoreResponse)
def get_report_by_id(report_id: int, db: Session = Depends(get_db)):
    """
    Get a specific report by its ID.
    """
    # Fetch the report by ID
    report = Report.get_report_by_id(db, report_id=report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    # Fetch the quiz name
    quiz = db.query(Quiz).filter(Quiz.id == report.quiz_id).first()
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found")

    # Serialize the data
    return {
        "quiz_name": quiz.name,
        "started_on": report.started_on.isoformat() if report.started_on else None,
        "completed_on": report.completed_on.isoformat() if report.completed_on else None,
        "score": report.score,
        "total_correct": report.total_correct,
        "total_incorrect": report.total_incorrect,
        "incorrect_answers": report.incorrect_answers,  # Assuming it's already JSON serializable
    }
