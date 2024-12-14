import random
from sqlalchemy import Column, Integer, ForeignKey, DateTime, Float, JSON
from sqlalchemy.ext.mutable import MutableList
from datetime import datetime
from sqlalchemy.orm import relationship, Session
from database import Base
from models.quiz import Quiz
from fastapi import HTTPException

class Report(Base):
    __tablename__ = "reports"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    quiz_id = Column(Integer, ForeignKey("quizzes.id"), nullable=False)
    started_on = Column(DateTime, default=datetime.utcnow)
    completed_on = Column(DateTime, nullable=True)
    score = Column(Float, nullable=True)
    total_correct = Column(Integer, default=0)
    total_incorrect = Column(Integer, default=0)
    incorrect_answers = Column(JSON, default=list)
    asked_questions = Column(MutableList.as_mutable(JSON), default=list)

    # Relationships
    user = relationship("User", back_populates="reports")
    quiz = relationship("Quiz", back_populates="reports")

    @staticmethod
    def create_report(db: Session, user_id: int, quiz_id: int) -> "Report":
        """
        Create a new report for a quiz session.
        """
        quiz = Quiz.get_quiz_by_id(db, quiz_id)
        if not quiz:
            raise HTTPException(status_code=404, detail="Quiz not found")

        quiz.increment_access_count()

        report = Report(
            user_id=user_id,
            quiz_id=quiz_id,
            started_on=datetime.utcnow(),
            asked_questions=[],
        )
        db.add(report)
        db.commit()
        db.refresh(report)
        return report

    def mark_completed(self, db: Session, score: float):
        """
        Mark the report as completed and update related quiz statistics.
        """
        if self.completed_on:
            raise HTTPException(
                status_code=400, detail="This report has already been completed."
            )

        self.completed_on = datetime.utcnow()
        self.score = score

        # Update quiz statistics
        quiz = db.query(Quiz).filter(Quiz.id == self.quiz_id).first()
        if quiz:
            quiz.increment_completion_count()
            quiz.update_statistics(score)

        db.commit()

    def log_answer(self, question: str, user_answer, correct_answer) -> str:
        """
        Log an answer as correct or incorrect and update totals.
        """
        # Convert user_answer and correct_answer to strings
        user_answer_str = str(user_answer).strip().lower()
        correct_answer_str = str(correct_answer).strip().lower()

        if user_answer_str == correct_answer_str:
            self.total_correct += 1
            return "correct"
        else:
            self.total_incorrect += 1
            self.incorrect_answers.append({
                "question": question,
                "user_answer": user_answer,  # Keep original value for clarity
                "correct_answer": correct_answer,  # Keep original value for clarity
            })
            return "incorrect"

    def update_asked_questions(self, question: str, db: Session):
        """
        Add a question to the list of asked questions.
        """
        if question not in self.asked_questions:
            self.asked_questions.append(question)
            db.commit()

    @classmethod
    def get_reports_by_user(cls, db: Session, user_id: int) -> list:
        """
        Fetch all reports for a given user.
        """
        return db.query(cls).filter(cls.user_id == user_id).all()

    @classmethod
    def get_reports_by_quiz(cls, db: Session, quiz_id: int) -> list:
        """
        Fetch all reports for a specific quiz.
        """
        return db.query(cls).filter(cls.quiz_id == quiz_id).all()

    @classmethod
    def get_report_by_id(cls, db: Session, report_id: int) -> "Report":
        """
        Fetch a report by its ID.
        """
        return db.query(cls).filter(cls.id == report_id).first()
