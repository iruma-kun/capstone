"""Assign tasks to users and attach task documents.

Revision ID: 0004_task_user_access
Revises: 0003_document_ai_analysis
Create Date: 2026-10-01
"""
from alembic import op
import sqlalchemy as sa

revision = "0004_task_user_access"
down_revision = "0003_document_ai_analysis"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("tasks") as batch_op:
        batch_op.add_column(sa.Column("assignee_id", sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column("document_id", sa.Integer(), nullable=True))
        batch_op.create_foreign_key("fk_tasks_assignee_id_users", "users", ["assignee_id"], ["id"])
        batch_op.create_foreign_key("fk_tasks_document_id_documents", "documents", ["document_id"], ["id"])
        batch_op.create_index("ix_tasks_assignee_id", ["assignee_id"])


def downgrade():
    with op.batch_alter_table("tasks") as batch_op:
        batch_op.drop_index("ix_tasks_assignee_id")
        batch_op.drop_constraint("fk_tasks_document_id_documents", type_="foreignkey")
        batch_op.drop_constraint("fk_tasks_assignee_id_users", type_="foreignkey")
        batch_op.drop_column("document_id")
        batch_op.drop_column("assignee_id")
