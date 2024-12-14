# Standard Library Imports
import os

# Third-Party Library Imports
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Application Imports
from database import Base, engine
from models import User, Quiz, Report  # Import models to ensure tables are created
from routes import user_routes, quiz_routes, report_routes

# Application Initialization
Base.metadata.create_all(bind=engine)  # Initialize database tables
root_path = os.getenv("ROOT_PATH", "/api")  # Default to "/" if ROOT_PATH is not set
app = FastAPI(
    title="StudyBuddy API",
    description="An API for quizzes and reports.",
    version="1.0.0",
    root_path=root_path,
    docs_url=f"{root_path}docs",  # Swagger UI
    openapi_url=f"{root_path}openapi.json"  # OpenAPI schema
)

User.create_admin()  # Ensure admin user exists

# CORS Middleware
origins = [
    "http://localhost",  # Frontend running on default port 80
    "http://localhost:3000",  # Development environment
    "http://127.0.0.1",  # Another local reference
    "http://46.101.235.156",  # DigitalOcean droplet
    "http://intcitium.de",  
    "https://intcitium.de"  # Include HTTPS if using SSL
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add Routers
app.include_router(user_routes.router, prefix="/users", tags=["Users"])
app.include_router(quiz_routes.router, prefix="/quizzes", tags=["Quizzes"])
app.include_router(report_routes.router, prefix="/reports", tags=["Reports"])

# Debug or initialization hooks (if any)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
