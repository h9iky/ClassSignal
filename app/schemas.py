"""Pydantic request and response schemas for the API."""

from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class SubjectCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    name: str = Field(min_length=1, max_length=100)
    description: str | None = None


class SubjectRead(SubjectCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int


class QuarterCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    school_year: str = Field(min_length=1, max_length=20, examples=["2025-2026"])
    number: int = Field(ge=1, le=4)
    starts_at: date | None = None
    ends_at: date | None = None

    @model_validator(mode="after")
    def dates_are_in_order(self) -> "QuarterCreate":
        if self.starts_at and self.ends_at and self.ends_at < self.starts_at:
            raise ValueError("ends_at must be on or after starts_at")
        return self


class QuarterRead(QuarterCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int


class TopicCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    subject_id: int = Field(gt=0)
    quarter_id: int = Field(gt=0)
    title: str = Field(min_length=1, max_length=200)
    description: str | None = None
    status: Literal["draft", "published", "archived"] = "draft"


class TopicUpdate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    subject_id: int | None = Field(default=None, gt=0)
    quarter_id: int | None = Field(default=None, gt=0)
    title: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = None
    status: Literal["draft", "published", "archived"] | None = None

    @model_validator(mode="after")
    def patch_has_valid_values(self) -> "TopicUpdate":
        if not self.model_fields_set:
            raise ValueError("at least one field must be provided")
        for field_name in self.model_fields_set:
            if field_name != "description" and getattr(self, field_name) is None:
                raise ValueError(f"{field_name} cannot be null")
        return self


class TopicRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    subject_id: int
    quarter_id: int
    title: str
    description: str | None
    status: str
    created_at: datetime
    updated_at: datetime
