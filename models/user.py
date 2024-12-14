# models.py

import os
from sqlalchemy import Column, Integer, String, DateTime
from datetime import datetime
from sqlalchemy.orm import relationship, Session
from database import Base, SessionLocal
from passlib.context import CryptContext
from utils.utils import verify_password
from sqlalchemy.sql import func
from models.quiz import Quiz
from models.report import Report


# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)  # Primary key
    username = Column(String, unique=True, index=True, nullable=False)
    password = Column(String, nullable=False)  # Store hashed passwords
    created_on = Column(DateTime, default=datetime.utcnow)
    is_admin = Column(Integer, default=0) # 1 if user is an admin, 0 otherwise
    max_quizzes = Column(Integer, default=int(os.getenv("MAX_QUIZZES_PER_USER", 10)))

    # Relationships
    quizzes = relationship("Quiz", back_populates="creator", cascade="all, delete-orphan")
    reports = relationship("Report", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User(username='{self.username}', created_on='{self.created_on}')>"


    def verify_password(self, plain_password: str, hashed_password: str):
        """Verify the provided password against the stored hashed password."""
        from passlib.context import CryptContext
        pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        return verify_password(plain_password, hashed_password)

    @classmethod
    def create_user(cls, db_session, username: str, hashed_password: str):
        """Create and save a new user."""
        user = cls(username=username, password=hashed_password)
        db_session.add(user)
        db_session.commit()
        return user

    @classmethod
    def get_user_by_username(cls, db_session, username: str):
        """Fetch a user by username."""
        return db_session.query(cls).filter(cls.username == username).first()

    @classmethod
    def get_user_by_id(cls, db_session, user_id: int):
        """Fetch a user by ID."""
        return db_session.query(cls).filter(cls.id == user_id).first()

    @classmethod
    def username_exists(cls, db_session, username: str):
        """Check if a username already exists."""
        return db_session.query(cls).filter(cls.username == username).first() is not None
    
    def to_dict(self, db: Session) -> dict:
        """
        Serialize user information to a dictionary.
        Query related quizzes and reports explicitly.
        """
        try:
            # Debugging outputs
            print(f"Processing user: {self.username}, ID: {self.id}")

            # Count related quizzes
            total_quizzes_created = db.query(func.count(Quiz.id)).filter(Quiz.created_by == self.id).scalar()
            total_reports_created = db.query(func.count(Report.id)).filter(Report.user_id == self.id).scalar()

            return {
                "id": self.id,
                "username": self.username,
                "created_on": self.created_on,
                "total_quizzes_created": total_quizzes_created,
                "total_reports_created": total_reports_created,
            }
        except Exception as e:
            print(f"Error serializing user {self.id}: {e}")
            raise

    def create_admin():
        """
        Create a default admin user if it doesn't already exist.
        """
        from sqlalchemy.exc import IntegrityError

        admin_username = os.getenv("ADMIN_USERNAME", "admin")
        admin_password = os.getenv("ADMIN_PASSWORD", "admin123")

        with SessionLocal() as db:
            try:
                # Check if admin user already exists
                existing_admin = db.query(User).filter_by(username=admin_username).first()
                if existing_admin:
                    print("Admin user already exists.")
                    return

                # Create admin user
                hashed_password = pwd_context.hash(admin_password)
                admin_user = User(username=admin_username, password=hashed_password, is_admin=1)
                db.add(admin_user)
                db.commit()
                print(f"Admin user '{admin_username}' created successfully.")
            except IntegrityError as e:
                db.rollback()
                print(f"Error creating admin user: {e}")

