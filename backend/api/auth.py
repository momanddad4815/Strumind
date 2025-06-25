from datetime import datetime, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from jose import JWTError, jwt
from pydantic import BaseModel, EmailStr
import secrets

router = APIRouter(prefix="/api/auth", tags=["authentication"])

# Mock database - In production, use proper database
fake_users_db = {}
active_tokens = set()

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT settings
SECRET_KEY = "your-secret-key-here"  # In production, use environment variable
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

# Pydantic models
class UserCreate(BaseModel):
    name: str
    email: EmailStr
    password: str
    company: Optional[str] = None

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class User(BaseModel):
    id: int
    name: str
    email: str
    company: Optional[str] = None
    created_at: datetime

class AuthResponse(BaseModel):
    access_token: str
    token_type: str
    user: User

class ForgotPasswordRequest(BaseModel):
    email: EmailStr

class ResetPasswordRequest(BaseModel):
    token: str
    password: str

# Utility functions
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def get_user_by_email(email: str):
    return fake_users_db.get(email)

def create_user(user_data: UserCreate):
    if user_data.email in fake_users_db:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    user_id = len(fake_users_db) + 1
    hashed_password = get_password_hash(user_data.password)
    
    user = {
        "id": user_id,
        "name": user_data.name,
        "email": user_data.email,
        "company": user_data.company,
        "hashed_password": hashed_password,
        "created_at": datetime.utcnow(),
        "is_active": True
    }
    
    fake_users_db[user_data.email] = user
    return user

def authenticate_user(email: str, password: str):
    user = get_user_by_email(email)
    if not user:
        return False
    if not verify_password(password, user["hashed_password"]):
        return False
    return user

async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    user = get_user_by_email(email)
    if user is None:
        raise credentials_exception
    return user

# API Routes
@router.post("/register", response_model=AuthResponse)
def register(user_data: UserCreate):
    try:
        user = create_user(user_data)
        
        # Create access token
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": user["email"]}, expires_delta=access_token_expires
        )
        
        active_tokens.add(access_token)
        
        user_response = User(
            id=user["id"],
            name=user["name"],
            email=user["email"],
            company=user["company"],
            created_at=user["created_at"]
        )
        
        return AuthResponse(
            access_token=access_token,
            token_type="bearer",
            user=user_response
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/login", response_model=AuthResponse)
def login(user_data: UserLogin):
    user = authenticate_user(user_data.email, user_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user["email"]}, expires_delta=access_token_expires
    )
    
    active_tokens.add(access_token)
    
    user_response = User(
        id=user["id"],
        name=user["name"],
        email=user["email"],
        company=user["company"],
        created_at=user["created_at"]
    )
    
    return AuthResponse(
        access_token=access_token,
        token_type="bearer",
        user=user_response
    )

@router.post("/logout")
def logout(token: str = Depends(oauth2_scheme)):
    active_tokens.discard(token)
    return {"message": "Successfully logged out"}

@router.get("/me", response_model=User)
def get_current_user_info(current_user: dict = Depends(get_current_user)):
    return User(
        id=current_user["id"],
        name=current_user["name"],
        email=current_user["email"],
        company=current_user["company"],
        created_at=current_user["created_at"]
    )

@router.post("/forgot-password")
def forgot_password(request: ForgotPasswordRequest):
    user = get_user_by_email(request.email)
    if not user:
        # Don't reveal if email exists
        return {"message": "If an account with that email exists, we've sent a password reset link."}
    
    # In production, send actual email
    reset_token = secrets.token_urlsafe(32)
    # Store reset token in database with expiration
    
    return {"message": "If an account with that email exists, we've sent a password reset link."}

@router.post("/reset-password")
def reset_password(request: ResetPasswordRequest):
    # In production, verify reset token from database
    # For now, just return success
    return {"message": "Password has been reset successfully."}
