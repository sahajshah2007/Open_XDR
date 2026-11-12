"""Persist isolated experiment runs, evidence links, and replay traces."""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision='0002_experiments'
down_revision='0001_unified_platform'
branch_labels=None
depends_on=None
JSON=sa.JSON().with_variant(postgresql.JSONB(),'postgresql')


def upgrade():
    bind=op.get_bind()
    tables=set(sa.inspect(bind).get_table_names())
    if 'experiment_runs' not in tables:
        op.create_table('experiment_runs',sa.Column('run_id',sa.UUID(),primary_key=True),sa.Column('scenario_id',sa.String(),nullable=False),sa.Column('name',sa.String(),nullable=False),sa.Column('seed',sa.Integer(),nullable=False),sa.Column('status',sa.String(),nullable=False),sa.Column('created_by',sa.String(),sa.ForeignKey('users.id'),nullable=False),sa.Column('created_at',sa.DateTime(timezone=True),server_default=sa.func.now(),nullable=False),sa.Column('completed_at',sa.DateTime(timezone=True)),sa.Column('snapshot',JSON,nullable=False),sa.Column('topology',JSON,nullable=False),sa.Column('metrics',JSON),sa.Column('verification',JSON),sa.Column('error',sa.String()))
        op.create_index('ix_experiment_runs_status','experiment_runs',['status'])
    if 'experiment_events' not in tables:
        op.create_table('experiment_events',sa.Column('event_id',sa.UUID(),sa.ForeignKey('events.event_id'),primary_key=True),sa.Column('run_id',sa.UUID(),sa.ForeignKey('experiment_runs.run_id'),nullable=False),sa.Column('position',sa.Integer(),nullable=False),sa.Column('label',sa.String(),nullable=False),sa.Column('expected_positive',sa.Boolean(),nullable=False),sa.Column('expected_techniques',JSON,nullable=False),sa.UniqueConstraint('run_id','position'))
        op.create_index('ix_experiment_events_run_id','experiment_events',['run_id'])
    if 'event_alerts' not in tables:
        op.create_table('event_alerts',sa.Column('event_id',sa.UUID(),sa.ForeignKey('events.event_id'),primary_key=True),sa.Column('alert_id',sa.UUID(),sa.ForeignKey('alerts.alert_id'),primary_key=True))
    if 'experiment_traces' not in tables:
        op.create_table('experiment_traces',sa.Column('trace_id',sa.UUID(),primary_key=True),sa.Column('run_id',sa.UUID(),sa.ForeignKey('experiment_runs.run_id'),nullable=False),sa.Column('event_id',sa.UUID(),sa.ForeignKey('events.event_id')),sa.Column('trace_key',sa.String(),nullable=False),sa.Column('ordinal',sa.Integer(),nullable=False),sa.Column('stage',sa.String(),nullable=False),sa.Column('message',sa.String(),nullable=False),sa.Column('payload',JSON,nullable=False),sa.Column('recorded_at',sa.DateTime(timezone=True),server_default=sa.func.now(),nullable=False),sa.UniqueConstraint('run_id','trace_key'))
        op.create_index('ix_experiment_traces_run_id','experiment_traces',['run_id'])


def downgrade():
    raise RuntimeError('Experiment evidence is retained. Export runs before explicitly removing experiment tables.')
