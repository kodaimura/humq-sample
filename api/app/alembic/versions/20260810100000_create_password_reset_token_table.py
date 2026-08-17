"""create password reset token table

Revision ID: 3f43b8fa0610
Revises: 2962e3d0bc06
Create Date: 2026-08-10 10:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "3f43b8fa0610"
down_revision: Union[str, Sequence[str], None] = "2962e3d0bc06"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "password_reset_token",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("account_id", sa.BigInteger, nullable=False),
        sa.Column("token_hash", sa.Text, nullable=False, unique=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            onupdate=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["account_id"], ["account.id"]),
    )
    op.create_index(
        "ix_password_reset_token_account_id",
        "password_reset_token",
        ["account_id"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_password_reset_token_account_id",
        table_name="password_reset_token",
    )
    op.drop_table("password_reset_token")
