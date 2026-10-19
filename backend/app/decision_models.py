"""Historial hipotético independiente; sin claves a telemetría o dispositivos."""

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import CheckConstraint, Column, Index, JSON, UniqueConstraint, text
from sqlmodel import Field, SQLModel

from .database import UTCDateTime, utc_now


class DecisionRun(SQLModel, table=True):
    __tablename__ = "decision_runs"
    __table_args__ = (CheckConstraint("source = 'hypothetical'", name="ck_decision_runs_source"),)

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    created_at: datetime = Field(default_factory=utc_now, sa_column=Column(UTCDateTime(), nullable=False))
    source: str = Field(default="hypothetical", max_length=20)
    parameters: dict = Field(sa_column=Column(JSON, nullable=False))
    result: dict = Field(sa_column=Column(JSON, nullable=False))
    engine_fingerprint: str = Field(max_length=64)
    snapshot_sha256: str = Field(max_length=64)


class DecisionReview(SQLModel, table=True):
    __tablename__ = "decision_reviews"
    __table_args__ = (
        UniqueConstraint("run_id", "alternative_id", name="uq_review_alternative"),
        CheckConstraint("decision IN ('approved', 'rejected')", name="ck_review_decision"),
        Index("uq_review_approved_run", "run_id", unique=True, sqlite_where=text("decision = 'approved'")),
    )

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    run_id: UUID = Field(foreign_key="decision_runs.id", ondelete="RESTRICT", index=True)
    alternative_id: str = Field(max_length=20)
    decision: str = Field(max_length=10)
    responsible: str = Field(max_length=120)
    reason: str = Field(max_length=2000)
    created_at: datetime = Field(default_factory=utc_now, sa_column=Column(UTCDateTime(), nullable=False))
