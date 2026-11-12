"""Baseline the existing OpenXDR schema and add ACDT processing/audit storage.

Existing tables are preserved when adopting the previously unversioned database.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0001_unified_platform"
down_revision = "95faffc550e2"
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    tables = set(sa.inspect(bind).get_table_names())
    if 'hosts' not in tables:
        op.create_table('hosts',
        sa.Column('host_id', sa.UUID(), nullable=False),
        sa.Column('host_name', sa.String(), nullable=False),
        sa.Column('os_name', sa.String(), nullable=True),
        sa.Column('os_version', sa.String(), nullable=True),
        sa.Column('agent_type', sa.String(), nullable=True),
        sa.Column('first_seen', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('last_seen', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('tags', sa.JSON().with_variant(postgresql.JSONB(astext_type=sa.Text()), 'postgresql'), server_default='{}', nullable=True),
        sa.Column('criticality', sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint('host_id')
        )
    if 'integration_settings' not in tables:
        op.create_table('integration_settings',
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('encrypted_value', sa.String(), nullable=False),
        sa.PrimaryKeyConstraint('name')
        )
    if 'users' not in tables:
        op.create_table('users',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('username', sa.String(), nullable=False),
        sa.Column('hashed_password', sa.String(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
        )
    if 'ix_users_username' not in {index["name"] for index in sa.inspect(bind).get_indexes('users')}:
        op.create_index(op.f('ix_users_username'), 'users', ['username'], unique=True)
    if 'events' not in tables:
        op.create_table('events',
        sa.Column('event_id', sa.UUID(), nullable=False),
        sa.Column('host_id', sa.UUID(), nullable=True),
        sa.Column('source', sa.String(), nullable=False),
        sa.Column('event_type', sa.String(), nullable=False),
        sa.Column('timestamp', sa.DateTime(timezone=True), nullable=False),
        sa.Column('normalized', sa.JSON().with_variant(postgresql.JSONB(astext_type=sa.Text()), 'postgresql'), nullable=False),
        sa.Column('raw', sa.JSON().with_variant(postgresql.JSONB(astext_type=sa.Text()), 'postgresql'), nullable=False),
        sa.ForeignKeyConstraint(['host_id'], ['hosts.host_id'], ),
        sa.PrimaryKeyConstraint('event_id')
        )
    if 'incidents' not in tables:
        op.create_table('incidents',
        sa.Column('incident_id', sa.UUID(), nullable=False),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('severity', sa.String(), nullable=False),
        sa.Column('confidence', sa.Integer(), nullable=False),
        sa.Column('status', sa.String(), nullable=False),
        sa.Column('host_id', sa.UUID(), nullable=True),
        sa.Column('first_seen', sa.DateTime(timezone=True), nullable=False),
        sa.Column('last_seen', sa.DateTime(timezone=True), nullable=False),
        sa.Column('attack_story', sa.JSON().with_variant(postgresql.JSONB(astext_type=sa.Text()), 'postgresql'), server_default='[]', nullable=True),
        sa.Column('mitre_techniques', sa.JSON().with_variant(postgresql.JSONB(astext_type=sa.Text()), 'postgresql'), server_default='[]', nullable=True),
        sa.Column('assignee_id', sa.String(), nullable=True),
        sa.Column('notes', sa.JSON().with_variant(postgresql.JSONB(astext_type=sa.Text()), 'postgresql'), server_default='[]', nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['assignee_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['host_id'], ['hosts.host_id'], ),
        sa.PrimaryKeyConstraint('incident_id')
        )
    if 'alerts' not in tables:
        op.create_table('alerts',
        sa.Column('alert_id', sa.UUID(), nullable=False),
        sa.Column('incident_id', sa.UUID(), nullable=True),
        sa.Column('host_id', sa.UUID(), nullable=True),
        sa.Column('rule_id', sa.String(), nullable=False),
        sa.Column('rule_name', sa.String(), nullable=False),
        sa.Column('source', sa.String(), nullable=True),
        sa.Column('severity', sa.String(), nullable=False),
        sa.Column('confidence', sa.String(), nullable=True),
        sa.Column('mitre_tactic', sa.String(), nullable=True),
        sa.Column('mitre_technique', sa.String(), nullable=True),
        sa.Column('source_ip', sa.String(), nullable=True),
        sa.Column('destination_ip', sa.String(), nullable=True),
        sa.Column('timestamp', sa.DateTime(timezone=True), nullable=False),
        sa.Column('raw_event', sa.JSON().with_variant(postgresql.JSONB(astext_type=sa.Text()), 'postgresql'), nullable=False),
        sa.Column('enrichment', sa.JSON().with_variant(postgresql.JSONB(astext_type=sa.Text()), 'postgresql'), server_default='{}', nullable=True),
        sa.ForeignKeyConstraint(['host_id'], ['hosts.host_id'], ),
        sa.ForeignKeyConstraint(['incident_id'], ['incidents.incident_id'], ),
        sa.PrimaryKeyConstraint('alert_id')
        )
    if 'pipeline_jobs' not in tables:
        op.create_table('pipeline_jobs',
        sa.Column('event_id', sa.UUID(), nullable=False),
        sa.Column('status', sa.String(), nullable=False),
        sa.Column('attempts', sa.Integer(), nullable=False),
        sa.Column('error', sa.String(), nullable=True),
        sa.Column('twin_status', sa.String(), nullable=False),
        sa.Column('twin_attempts', sa.Integer(), nullable=False),
        sa.Column('twin_error', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('processed_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['event_id'], ['events.event_id'], ),
        sa.PrimaryKeyConstraint('event_id')
        )
    if 'ix_pipeline_jobs_status' not in {index["name"] for index in sa.inspect(bind).get_indexes('pipeline_jobs')}:
        op.create_index(op.f('ix_pipeline_jobs_status'), 'pipeline_jobs', ['status'], unique=False)
    if 'ix_pipeline_jobs_twin_status' not in {index["name"] for index in sa.inspect(bind).get_indexes('pipeline_jobs')}:
        op.create_index(op.f('ix_pipeline_jobs_twin_status'), 'pipeline_jobs', ['twin_status'], unique=False)
    if 'response_actions' not in tables:
        op.create_table('response_actions',
        sa.Column('action_id', sa.UUID(), nullable=False),
        sa.Column('incident_id', sa.UUID(), nullable=False),
        sa.Column('policy_id', sa.String(), nullable=False),
        sa.Column('action', sa.String(), nullable=False),
        sa.Column('autonomy', sa.String(), nullable=False),
        sa.Column('status', sa.String(), nullable=False),
        sa.Column('requested_by', sa.String(), nullable=False),
        sa.Column('result', sa.JSON().with_variant(postgresql.JSONB(astext_type=sa.Text()), 'postgresql'), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('executed_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['incident_id'], ['incidents.incident_id'], ),
        sa.ForeignKeyConstraint(['requested_by'], ['users.id'], ),
        sa.PrimaryKeyConstraint('action_id'),
        sa.UniqueConstraint('incident_id', 'policy_id', 'action')
        )
    if 'ix_response_actions_incident_id' not in {index["name"] for index in sa.inspect(bind).get_indexes('response_actions')}:
        op.create_index(op.f('ix_response_actions_incident_id'), 'response_actions', ['incident_id'], unique=False)

    if 'ix_events_timestamp' not in {index["name"] for index in sa.inspect(bind).get_indexes('events')}:
        op.create_index('ix_events_timestamp', 'events', ['timestamp'])
    if 'ix_events_host_timestamp' not in {index["name"] for index in sa.inspect(bind).get_indexes('events')}:
        op.create_index('ix_events_host_timestamp', 'events', ['host_id', 'timestamp'])

    if 'ix_alerts_incident_timestamp' not in {index["name"] for index in sa.inspect(bind).get_indexes('alerts')}:
        op.create_index('ix_alerts_incident_timestamp', 'alerts', ['incident_id', 'timestamp'])
    if 'ix_alerts_source_timestamp' not in {index["name"] for index in sa.inspect(bind).get_indexes('alerts')}:
        op.create_index('ix_alerts_source_timestamp', 'alerts', ['source_ip', 'timestamp'])

    if 'ix_incidents_host_status_last_seen' not in {index["name"] for index in sa.inspect(bind).get_indexes('incidents')}:
        op.create_index('ix_incidents_host_status_last_seen', 'incidents', ['host_id', 'status', 'last_seen'])


def downgrade():
    # A baseline downgrade is intentionally non-destructive. Never delete a
    # user's pre-merge event store when rolling back the migration marker.
    pass
