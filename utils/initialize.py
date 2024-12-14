import os
from sqlalchemy.orm import Session
from database import SessionLocal, engine
from models import User
from utils.utils import hash_password

def create_admin_user():
    """
    Create the default admin user based on the environment variable `ADMIN_PASSWORD`.
    If the admin user already exists, skip creation.
    """
    session: Session = SessionLocal()

    try:
        # Check if an admin user already exists
        admin_user = session.query(User).filter(User.username == "admin").first()
        if admin_user:
            print("Admin user already exists. Skipping creation.")
            return

        # Fetch the password from environment variables
        admin_password = os.getenv("ADMIN_PASSWORD")
        if not admin_password:
            print("Environment variable ADMIN_PASSWORD not set.")
            return

        # Create the admin user
        hashed_password = hash_password(admin_password)
        admin_user = User(
            username="admin",
            password=hashed_password,
            is_admin=1,  # Assuming 1 indicates admin
            created_on=None  # Set created_on to None; it will default to current timestamp
        )
        session.add(admin_user)
        session.commit()
        print("Admin user created successfully.")
    except Exception as e:
        print(f"Error creating admin user: {e}")
    finally:
        session.close()

# Run the function when the script is executed
if __name__ == "__main__":
    create_admin_user()
