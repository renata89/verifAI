# Sample 1: Login system
# Acceptance Criteria:
# - User can register with email and password
# - Password must be at least 8 characters
# - Welcome email sent after registration

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr

router = APIRouter()

class RegisterRequest(BaseModel):
    email: str
    password: str
    name: str

class UserResponse(BaseModel):
    id: int
    email: str
    name: str

@router.post("/register", response_model=UserResponse, status_code=201)
async def register_user(req: RegisterRequest):
    # Check password length (AC #2)
    if len(req.password) < 8:
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters")
    
    # Create user in database (AC #1)
    user_id = await database.execute(
        "INSERT INTO users (email, password, name) VALUES (:e, :p, :n)",
        {"e": req.email, "p": hash_password(req.password), "n": req.name}
    )
    
    # BUG: Missing welcome email (AC #3 not implemented!)
    # Should be: await send_welcome_email(req.email, req.name)
    
    return {"id": user_id, "email": req.email, "name": req.name}
