"""Save immutable detection configurations without altering existing evidence."""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '0003_detection_profiles'
down_revision = '0002_experiments'
branch_labels = None
depends_on = None


def upgrade():
    if 'detection_profiles' not in sa.inspect(op.get_bind()).get_table_names():
        op.create_table(
            'detection_profiles',
            sa.Column('profile_id', sa.UUID(), primary_key=True),
            sa.Column('name', sa.String(), nullable=False),
            sa.Column('description', sa.String(), nullable=False),
            sa.Column('created_by', sa.String(), sa.ForeignKey('users.id'), nullable=False),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.Column('snapshot', sa.JSON().with_variant(postgresql.JSONB(), 'postgresql'), nullable=False),
        )


def downgrade():
    raise RuntimeError('Saved detection configurations are evidence. Export before explicitly removing them.')
