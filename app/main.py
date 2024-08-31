from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app import models, auth
from app.database import engine
from fastapi.security import OAuth2PasswordRequestForm
from datetime import timedelta
from pydantic import BaseModel
from typing import List
from app.auth import get_password_hash, get_current_user
from app.database import get_db
from app import schemas

app = FastAPI()

models.Base.metadata.create_all(bind=engine)


class UserCreate(BaseModel):
    username: str
    password: str


@app.post("/register/")
async def register(user: UserCreate, db: Session = Depends(get_db)):
    existing_user = db.query(models.User).filter(models.User.username == user.username).first()
    if existing_user:
        raise HTTPException(status_code=400,
                            detail="Username already registered")
    hashed_password = get_password_hash(user.password)
    new_user = models.User(username=user.username,
                           hashed_password=hashed_password)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return {"msg": "User created successfully"}


@app.post("/token")
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(),
                                 db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.username == form_data.username).first()
    if not user or not auth.verify_password(form_data.password,
                                            user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=auth.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = auth.create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


@app.post("/notes/", response_model=schemas.Note)
async def create_note(note: schemas.NoteCreate, db: Session = Depends(get_db),
                      current_user: models.User = Depends(get_current_user)):
    new_note = models.Note(
        title=note.title,
        content=note.content,
        owner_id=current_user.id
    )
    db.add(new_note)
    db.commit()
    db.refresh(new_note)
    return new_note


@app.get("/notes/")
async def read_notes(skip: int = 0, limit: int = 10,
                     token: str = Depends(auth.oauth2_scheme),
                     db: Session = Depends(get_db)):
    username = auth.get_username_from_token(token)
    user = db.query(models.User).filter(models.User.username == username).first()
    if user is None:
        raise HTTPException(status_code=400, detail="User not found")
    notes = db.query(models.Note).filter(models.Note.owner_id == user.id).offset(skip).limit(limit).all()
    return notes


@app.get("/users/{user_id}/notes/",
         response_model=List[schemas.Note])
async def get_user_notes(user_id: int, db: Session = Depends(get_db)):
    notes = db.query(models.Note).filter(models.Note.owner_id == user_id).all()
    return notes
