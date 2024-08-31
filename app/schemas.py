from pydantic import BaseModel


class NoteBase(BaseModel):
    title: str
    content: str


class NoteCreate(NoteBase):
    title: str
    content: str


class Note(NoteBase):
    id: int
    owner_id: int

    class Config:
        orm_mode = True
