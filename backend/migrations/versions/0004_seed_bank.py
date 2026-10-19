"""Banco biocultural sin precarga: pasaportes, pesos, evaluaciones y decisiones."""

from alembic import op
import sqlalchemy as sa

revision = '0004_seeds'
down_revision = '0003_decisions'
branch_labels = None
depends_on = None


def identifier():
    return sa.Column('id', sa.Uuid(), primary_key=True)


def timestamp():
    return sa.Column('created_at', sa.DateTime(), nullable=False)


def lot_reference():
    return sa.Column('lot_id', sa.Uuid(), sa.ForeignKey('seed_lots.id', ondelete='RESTRICT'), nullable=False)


def upgrade():
    op.create_table('seed_lots', identifier(),
                    sa.Column('code', sa.String(120), nullable=False),
                    sa.Column('source_kind', sa.String(20), nullable=False),
                    sa.Column('revision', sa.Integer(), nullable=False),
                    sa.Column('passport', sa.JSON(), nullable=False), timestamp(),
                    sa.Column('updated_at', sa.DateTime(), nullable=False),
                    sa.UniqueConstraint('code', name='uq_seed_code'),
                    sa.CheckConstraint("source_kind IN ('real', 'hypothetical')", name='ck_seed_source'),
                    sa.CheckConstraint('revision >= 1', name='ck_seed_revision'))
    op.create_table('seed_lot_revisions', identifier(), lot_reference(),
                    sa.Column('revision', sa.Integer(), nullable=False),
                    sa.Column('passport', sa.JSON(), nullable=False), timestamp(),
                    sa.UniqueConstraint('lot_id', 'revision', name='uq_seed_revision'))
    op.create_table('seed_weight_profiles', identifier(),
                    sa.Column('weights', sa.JSON(), nullable=False),
                    sa.Column('responsible', sa.String(120), nullable=False),
                    sa.Column('reason', sa.String(2000), nullable=False), timestamp())
    op.create_table('seed_assessments', identifier(), lot_reference(),
                    sa.Column('lot_revision', sa.Integer(), nullable=False),
                    sa.Column('weight_profile_id', sa.Uuid(), sa.ForeignKey('seed_weight_profiles.id', ondelete='RESTRICT')),
                    sa.Column('weights', sa.JSON(), nullable=False),
                    sa.Column('scores', sa.JSON(), nullable=False),
                    sa.Column('total', sa.Float()),
                    sa.Column('responsible', sa.String(120), nullable=False), timestamp(),
                    sa.ForeignKeyConstraint(['lot_id', 'lot_revision'],
                        ['seed_lot_revisions.lot_id', 'seed_lot_revisions.revision'],
                        ondelete='RESTRICT', name='fk_assessment_passport_revision'))
    op.create_table('seed_decisions', identifier(), lot_reference(),
                    sa.Column('action', sa.String(20), nullable=False),
                    sa.Column('responsible', sa.String(120), nullable=False),
                    sa.Column('reason', sa.String(2000), nullable=False),
                    sa.Column('snapshot', sa.JSON(), nullable=False), timestamp(),
                    sa.CheckConstraint("action IN ('conservar', 'sembrar', 'retirar', 'repetir_prueba', 'seleccionar')", name='ck_seed_decision'))
    for table in ('seed_lot_revisions', 'seed_assessments', 'seed_decisions'):
        op.create_index(f'ix_{table}_lot_id', table, ['lot_id'])


def downgrade():
    raise RuntimeError('Reversión destructiva deshabilitada: conservar pasaportes y decisiones humanas.')
