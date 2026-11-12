"""Recognize the migration marker used by existing OpenXDR databases.

The original migration script was absent from the supplied source tree. This
compatibility revision does not recreate, drop, stamp, or alter existing tables.
The following unified-platform migration creates any missing tables on fresh
installations and adds the new processing/audit tables to existing installations.
"""

revision = "95faffc550e2"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
