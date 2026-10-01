"""Create the initial Lexflow schema.

Revision ID: 0001_initial
Revises:
Create Date: 2026-09-29
"""
from alembic import op
import sqlalchemy as sa

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("role", sa.String(30), nullable=False),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)
    op.create_table(
        "clients",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("phone", sa.String(40), nullable=False),
        sa.Column("company", sa.String(120), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_clients_name", "clients", ["name"])
    op.create_table(
        "matters",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("reference", sa.String(30), nullable=False),
        sa.Column("title", sa.String(180), nullable=False),
        sa.Column("practice_area", sa.String(80), nullable=False),
        sa.Column("status", sa.Enum("intake", "active", "review", "closed", name="matterstatus"), nullable=False),
        sa.Column("priority", sa.String(20), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("next_deadline", sa.Date(), nullable=True),
        sa.Column("client_id", sa.Integer(), sa.ForeignKey("clients.id"), nullable=False),
        sa.Column("assigned_to", sa.String(100), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_matters_reference", "matters", ["reference"], unique=True)
    op.create_index("ix_matters_title", "matters", ["title"])
    op.create_table(
        "tasks",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("title", sa.String(180), nullable=False),
        sa.Column("due_date", sa.Date(), nullable=True),
        sa.Column("completed", sa.Boolean(), nullable=False),
        sa.Column("assignee", sa.String(100), nullable=False),
        sa.Column("matter_id", sa.Integer(), sa.ForeignKey("matters.id"), nullable=False),
    )
    op.create_table(
        "documents",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(180), nullable=False),
        sa.Column("category", sa.String(60), nullable=False),
        sa.Column("size", sa.String(20), nullable=False),
        sa.Column("uploaded_at", sa.DateTime(), nullable=False),
        sa.Column("matter_id", sa.Integer(), sa.ForeignKey("matters.id"), nullable=False),
    )


def downgrade():
    op.drop_table("documents")
    op.drop_table("tasks")
    op.drop_index("ix_matters_title", table_name="matters")
    op.drop_index("ix_matters_reference", table_name="matters")
    op.drop_table("matters")
    op.drop_index("ix_clients_name", table_name="clients")
    op.drop_table("clients")
    op.drop_index("ix_users_email", table_name="users")
    op.drop_table("users")
