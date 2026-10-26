"""HTTP endpoints for subjects, quarters, and topics."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Quarter, Subject, Topic
from app.schemas import (
    QuarterCreate,
    QuarterRead,
    SubjectCreate,
    SubjectRead,
    TopicCreate,
    TopicRead,
    TopicUpdate,
)

router = APIRouter(prefix="/api/v1")
DatabaseSession = Annotated[Session, Depends(get_db)]


def _commit_or_conflict(db: Session, detail: str) -> None:
    try:
        db.commit()
    except IntegrityError as error:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=detail) from error


@router.get("/health")
def health_check() -> dict[str, str]:
    """Report that the API process is responding (not a database readiness check)."""
    return {"status": "ok"}


@router.get("/subjects", response_model=list[SubjectRead])
def list_subjects(db: DatabaseSession) -> list[Subject]:
    return list(db.scalars(select(Subject).order_by(Subject.name)))


@router.post("/subjects", response_model=SubjectRead, status_code=status.HTTP_201_CREATED)
def create_subject(data: SubjectCreate, db: DatabaseSession) -> Subject:
    subject = Subject(name=data.name.strip(), description=data.description)
    if not subject.name:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="name cannot be blank")
    db.add(subject)
    _commit_or_conflict(db, "A subject with this name already exists")
    db.refresh(subject)
    return subject


@router.get("/quarters", response_model=list[QuarterRead])
def list_quarters(db: DatabaseSession) -> list[Quarter]:
    statement = select(Quarter).order_by(Quarter.school_year, Quarter.number)
    return list(db.scalars(statement))


@router.post("/quarters", response_model=QuarterRead, status_code=status.HTTP_201_CREATED)
def create_quarter(data: QuarterCreate, db: DatabaseSession) -> Quarter:
    quarter = Quarter(**data.model_dump())
    db.add(quarter)
    _commit_or_conflict(db, "This quarter already exists for the school year")
    db.refresh(quarter)
    return quarter


@router.get("/topics", response_model=list[TopicRead])
def list_topics(
    db: DatabaseSession,
    subject_id: Annotated[int | None, Query(gt=0)] = None,
    quarter_id: Annotated[int | None, Query(gt=0)] = None,
) -> list[Topic]:
    statement = select(Topic)
    if subject_id is not None:
        statement = statement.where(Topic.subject_id == subject_id)
    if quarter_id is not None:
        statement = statement.where(Topic.quarter_id == quarter_id)
    return list(db.scalars(statement.order_by(Topic.id)))


@router.post("/topics", response_model=TopicRead, status_code=status.HTTP_201_CREATED)
def create_topic(data: TopicCreate, db: DatabaseSession) -> Topic:
    if db.get(Subject, data.subject_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Subject not found")
    if db.get(Quarter, data.quarter_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Quarter not found")

    topic = Topic(**data.model_dump())
    db.add(topic)
    db.commit()
    db.refresh(topic)
    return topic


@router.get("/topics/{topic_id}", response_model=TopicRead)
def get_topic(topic_id: int, db: DatabaseSession) -> Topic:
    topic = db.get(Topic, topic_id)
    if topic is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Topic not found")
    return topic


@router.patch("/topics/{topic_id}", response_model=TopicRead)
def update_topic(topic_id: int, data: TopicUpdate, db: DatabaseSession) -> Topic:
    topic = db.get(Topic, topic_id)
    if topic is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Topic not found")

    changes = data.model_dump(exclude_unset=True)
    if "subject_id" in changes and db.get(Subject, changes["subject_id"]) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Subject not found")
    if "quarter_id" in changes and db.get(Quarter, changes["quarter_id"]) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Quarter not found")

    for field_name, value in changes.items():
        setattr(topic, field_name, value)
    db.commit()
    db.refresh(topic)
    return topic
