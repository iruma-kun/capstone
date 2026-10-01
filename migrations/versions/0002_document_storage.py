"""Add uploaded document storage fields.

Revision ID: 0002_document_storage
Revises: 0001_initial
Create Date: 2026-09-30
"""
from alembic import op
import sqlalchemy as sa

revision = "0002_document_storage"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("documents", sa.Column("storage_key", sa.String(255), nullable=True))
    op.add_column("documents", sa.Column("content_type", sa.String(120), nullable=True))


def downgrade():
    op.drop_column("documents", "content_type")
    op.drop_column("documents", "storage_key")
