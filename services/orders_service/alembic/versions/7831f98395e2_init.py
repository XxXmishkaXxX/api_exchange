"""init

Revision ID: 7831f98395e2
Revises: 
Create Date: 2025-03-18 16:14:33.861365

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7831f98395e2'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('orders', sa.Column('status', sa.Enum('NEW', 'FILLED', 'PENDING', 'REJECTED', name='statusorder'), nullable=False))
    op.add_column('orders', sa.Column('ticker_id', sa.Integer(), nullable=False))
    op.create_foreign_key(None, 'orders', 'tickers', ['ticker_id'], ['id'])
    op.drop_column('orders', 'ticker')
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('orders', sa.Column('ticker', sa.VARCHAR(length=10), autoincrement=False, nullable=False))
    op.drop_constraint(None, 'orders', type_='foreignkey')
    op.drop_column('orders', 'ticker_id')
    op.drop_column('orders', 'status')
    # ### end Alembic commands ###
