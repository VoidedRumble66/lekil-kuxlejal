"""Banco local separado de sensores. UUID estables para futuras asociaciones de cultivo."""

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import CheckConstraint, Column, ForeignKeyConstraint, JSON, UniqueConstraint
from sqlmodel import Field, SQLModel

from .database import UTCDateTime, utc_now


class SeedLot(SQLModel, table=True):
    __tablename__ = 'seed_lots'
    __table_args__ = (
        UniqueConstraint('code', name='uq_seed_code'),
        CheckConstraint("source_kind IN ('real', 'hypothetical')", name='ck_seed_source'),
        CheckConstraint('revision >= 1', name='ck_seed_revision'),
    )
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    code: str = Field(max_length=120)
    source_kind: str = Field(max_length=20)
    revision: int = Field(default=1)
    passport: dict = Field(sa_column=Column(JSON, nullable=False))
    created_at: datetime = Field(default_factory=utc_now, sa_column=Column(UTCDateTime(), nullable=False))
    updated_at: datetime = Field(default_factory=utc_now, sa_column=Column(UTCDateTime(), nullable=False))


class SeedLotRevision(SQLModel, table=True):
    __tablename__ = 'seed_lot_revisions'
    __table_args__ = (UniqueConstraint('lot_id', 'revision', name='uq_seed_revision'),)
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    lot_id: UUID = Field(foreign_key='seed_lots.id', ondelete='RESTRICT', index=True)
    revision: int
    passport: dict = Field(sa_column=Column(JSON, nullable=False))
    created_at: datetime = Field(default_factory=utc_now, sa_column=Column(UTCDateTime(), nullable=False))


class SeedWeightProfile(SQLModel, table=True):
    __tablename__ = 'seed_weight_profiles'
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    weights: dict = Field(sa_column=Column(JSON, nullable=False))
    responsible: str = Field(max_length=120)
    reason: str = Field(max_length=2000)
    created_at: datetime = Field(default_factory=utc_now, sa_column=Column(UTCDateTime(), nullable=False))


class SeedAssessment(SQLModel, table=True):
    __tablename__ = 'seed_assessments'
    __table_args__ = (ForeignKeyConstraint(['lot_id', 'lot_revision'],
                        ['seed_lot_revisions.lot_id', 'seed_lot_revisions.revision'],
                        ondelete='RESTRICT', name='fk_assessment_passport_revision'),)
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    lot_id: UUID = Field(foreign_key='seed_lots.id', ondelete='RESTRICT', index=True)
    lot_revision: int
    weight_profile_id: UUID | None = Field(default=None, foreign_key='seed_weight_profiles.id', ondelete='RESTRICT')
    weights: dict = Field(sa_column=Column(JSON, nullable=False))
    scores: dict = Field(sa_column=Column(JSON, nullable=False))
    total: float | None = None
    responsible: str = Field(max_length=120)
    created_at: datetime = Field(default_factory=utc_now, sa_column=Column(UTCDateTime(), nullable=False))


class SeedDecision(SQLModel, table=True):
    __tablename__ = 'seed_decisions'
    __table_args__ = (CheckConstraint("action IN ('conservar', 'sembrar', 'retirar', 'repetir_prueba', 'seleccionar')", name='ck_seed_decision'),)
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    lot_id: UUID = Field(foreign_key='seed_lots.id', ondelete='RESTRICT', index=True)
    action: str = Field(max_length=20)
    responsible: str = Field(max_length=120)
    reason: str = Field(max_length=2000)
    snapshot: dict = Field(sa_column=Column(JSON, nullable=False))
    created_at: datetime = Field(default_factory=utc_now, sa_column=Column(UTCDateTime(), nullable=False))
