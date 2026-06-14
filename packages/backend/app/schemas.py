"""Pydantic 입출력 스키마 (FR-5)."""
from __future__ import annotations

import enum
from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, field_validator


def _enum_value(v: Any) -> Any:
    return v.value if isinstance(v, enum.Enum) else v


class JobCreate(BaseModel):
    product_id: int | None = None
    style: str = "정보형"
    input_props: dict[str, Any] | None = None


class JobOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    product_id: int | None
    style: str
    status: str
    quota_date: date
    video_path: str | None
    error: str | None
    created_at: datetime
    approved_by: str | None
    approved_at: datetime | None
    published_at: datetime | None

    @field_validator("style", "status", mode="before")
    @classmethod
    def _coerce_enum(cls, v: Any) -> Any:
        return _enum_value(v)
