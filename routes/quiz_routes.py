import os
import random
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy import func
from sqlalchemy.orm import Session
from database import get_db
import pandas as pd
from models import User, Quiz, Report
from dependencies import get_current_user

router = APIRouter()

# Define the maximum number of quizzes a user can upload
MAX_QUIZZES_PER_USER = int(os.getenv("MAX_QUIZZES_PER_USER", 10))  # Default is 10


@router.get("/", status_code=status.HTTP_200_OK)
def list_all_quizzes(db: Session = Depends(get_db)):
    """
    List all quizzes.
    """
    quizzes = Quiz.get_all_quizzes(db)
    return [
        {
            "id": quiz.id,
            "name": quiz.name,
            "created_on": quiz.created_on,
            "total_questions": quiz.total_questions,
        }
        for quiz in quizzes
    ]


@router.post("/upload-csv", status_code=status.HTTP_201_CREATED)
async def upload_csv(
    file: UploadFile = File(...),
    name: str = Form(...),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Upload a CSV file to create a new quiz with a unique name.
    """
    # Check if the quiz limit has been reached
    user_quiz_count = db.query(func.count(Quiz.id)).filter(Quiz.created_by == current_user.id).scalar()
    if user_quiz_count >= MAX_QUIZZES_PER_USER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"You have reached the limit of {MAX_QUIZZES_PER_USER} quizzes."
        )
    if Quiz.get_quiz_by_name(db, name):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Quiz name already exists. Please choose another name.",
        )

    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="File must be a CSV.")

    try:
        # Read the CSV into a DataFrame
        df = pd.read_csv(file.file)
        if "Q" not in df.columns or "A" not in df.columns:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="CSV must contain 'Q' and 'A' columns.",
            )

        # Create the quiz
        questions = dict(zip(df["Q"], df["A"]))
        quiz = Quiz(
            name=name,
            questions=questions,
            total_questions=len(questions),
            created_by=current_user.id,
        )
        quiz.set_questions(questions)
        db.add(quiz)
        db.commit()
        db.refresh(quiz)

        return {
            "message": "Quiz created successfully",
            "total_questions": quiz.total_questions,
            "id": quiz.id,
            "name": name,
            "created_on": quiz.created_on,
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing file: {str(e)}",
        )


@router.post("/start", status_code=status.HTTP_201_CREATED)
def start_quiz(
    quiz_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Start a new quiz session (create a report).
    """

    # Get the report and quiz to start the quiz with a first question
    report = Report.create_report(db=db, user_id=current_user.id, quiz_id=quiz_id)
    quiz = Quiz.get_quiz_by_id(db, quiz_id)
    all_questions = [q for q in quiz.get_questions().keys()]
    next_question = random.choice(all_questions)
    report.update_asked_questions(next_question, db)

    return {
        "status": "in_progress",
        "total_correct": report.total_correct,
        "total_incorrect": report.total_incorrect,
        "next_question": next_question,
        "total_questions": quiz.total_questions,
        "report_id": report.id,
        "started_on": report.started_on
    }


@router.post("/{quiz_id}/submit-answer")
def submit_answer(
    quiz_id: int,
    report_id: int,
    question: str,
    user_answer: str,
    db: Session = Depends(get_db),
):
    """
    Submit an answer and determine the next question or completion status.
    """
    report = Report.get_report_by_id(db, report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    quiz = Quiz.get_quiz_by_id(db, quiz_id)
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found")

    all_questions = quiz.get_questions()
    correct_answer = all_questions.get(question)
    if not correct_answer:
        raise HTTPException(status_code=400, detail="Invalid question submitted")

    # Log the answer
    result = report.log_answer(question, user_answer, correct_answer)

    # Determine remaining questions
    remaining_questions = [
        q for q in all_questions.keys() if q not in report.asked_questions
    ]

    if not remaining_questions:
        # Quiz completed
        score = (report.total_correct / quiz.total_questions) * 100
        report.mark_completed(db, score)
        return {
            "status": "completed",
            "message": "Quiz completed!",
            "total_correct": report.total_correct,
            "total_incorrect": report.total_incorrect,
            "score": score,
        }

    # Get the next question
    next_question = random.choice(remaining_questions)
    report.update_asked_questions(next_question, db)

    return {
        "status": "in_progress",
        "result": result,
        "correct_answer": correct_answer if result == "incorrect" else None,
        "total_correct": report.total_correct,
        "total_incorrect": report.total_incorrect,
        "next_question": next_question,
        "total_questions": quiz.total_questions,
    }


@router.get("/{quiz_id}", status_code=status.HTTP_200_OK)
def get_quiz_details(quiz_id: int, db: Session = Depends(get_db)):
    """
    Get details of a specific quiz.
    """
    quiz = Quiz.get_quiz_by_id(db, quiz_id)
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found")

    return {
        "id": quiz.id,
        "name": quiz.name,
        "created_on": quiz.created_on,
        "total_questions": quiz.total_questions,
        "times_accessed": quiz.times_accessed,
        "times_completed": quiz.times_completed,
        "highest_score": quiz.highest_score,
        "average_score": quiz.average_score,
    }
