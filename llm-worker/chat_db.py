from dataclasses import dataclass
from enum import Enum
from typing import List
from sqlalchemy import Column, ForeignKey, Integer, String, Text, Enum as SQLAlchemyEnum
from sqlalchemy.orm import Session
from sqlalchemy.ext.declarative import declarative_base
DBBase = declarative_base()

class MsgRole(Enum):
    ASSISTANT = "assistant"
    USER = "user"

class RecordType(Enum):
    FILE = "file"
    OPENAPI_SCHEMA = "openapi_schema"
    API_HANDLER = "api_handler"

class Project(DBBase):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True)
    name = Column(String)

class Message(DBBase):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey("projects.id"))
    role = Column(SQLAlchemyEnum(MsgRole))
    content = Column(Text)

class ProjectContext(DBBase):
    __tablename__ = "project_context_records"

    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey("projects.id"))
    record_type = Column(SQLAlchemyEnum(RecordType))
    service_name = Column(String)
    data = Column(Text)

@dataclass
class ProjectData:
    messages: List[Message]
    context: List[ProjectContext]

@dataclass
class NewMessage:
    role: MsgRole
    project_id: int
    content: str

@dataclass
class NewProjectContext:
    record_type: RecordType
    project_id: int
    service_name: str
    data: str

def get_project_list(db: Session) -> List[Project]:
    return db.query(Project).all()

def get_project_data(db: Session, project_id: int) -> ProjectData:
    messages = db.query(Message).filter(Message.project_id == project_id).all()
    ctx = db.query(ProjectContext).filter(ProjectContext.project_id == project_id).all()
    return ProjectData(messages=messages, context=ctx)

def add_messages(db: Session, messages: List[NewMessage]):
    for msg in messages:
        db_item = Message(**msg.__dict__)
        db.add(db_item)
    db.commit()

def add_context(db: Session, records: List[NewProjectContext]):
    for r in records:
        db_item = ProjectContext(**r.__dict__)
        db.add(db_item)
    db.commit()
