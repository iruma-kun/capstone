"""Add structured Ollama document analysis.

Revision ID: 0003_document_ai_analysis
Revises: 0002_document_storage
Create Date: 2026-09-30
"""
from alembic import op
import sqlalchemy as sa

revision = "0003_document_ai_analysis"
down_revision = "0002_document_storage"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("documents", sa.Column("ai_analysis", sa.Text(), nullable=True))
    op.add_column("documents", sa.Column("ai_model", sa.String(120), nullable=True))
    op.add_column("documents", sa.Column("ai_analyzed_at", sa.DateTime(), nullable=True))


def downgrade():
    op.drop_column("documents", "ai_analyzed_at")
    op.drop_column("documents", "ai_model")
    op.drop_column("documents", "ai_analysis")
