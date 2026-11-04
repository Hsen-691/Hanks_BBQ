"""items and categories can be limited to certain branches

Revision ID: b41e7c9a52d3
Revises: 30eed270bcda
Create Date: 2026-10-25 12:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b41e7c9a52d3'
down_revision: Union[str, None] = '30eed270bcda'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Every existing category and item stays on ALL branches until you change it.
    op.add_column('categories', sa.Column('all_branches', sa.Boolean(), server_default=sa.true(), nullable=False))
    op.add_column('products', sa.Column('all_branches', sa.Boolean(), server_default=sa.true(), nullable=False))
    op.create_table('category_branches',
        sa.Column('category_id', sa.Uuid(), nullable=False),
        sa.Column('branch_id', sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(['branch_id'], ['branches.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['category_id'], ['categories.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('category_id', 'branch_id'),
    )
    op.create_table('product_branches',
        sa.Column('product_id', sa.Uuid(), nullable=False),
        sa.Column('branch_id', sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(['branch_id'], ['branches.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['product_id'], ['products.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('product_id', 'branch_id'),
    )


def downgrade() -> None:
    op.drop_table('product_branches')
    op.drop_table('category_branches')
    op.drop_column('products', 'all_branches')
    op.drop_column('categories', 'all_branches')