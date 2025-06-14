"""Initial migration

Revision ID: ece80320bdaa
Revises: 
Create Date: 2025-05-20 11:09:20.625440

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ece80320bdaa'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('assets',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('ticker', sa.String(), nullable=False),
    sa.Column('name', sa.String(), nullable=False),
    sa.Column('status', sa.Enum('ACTIVATE', 'DEACTIVATE', name='assetstatus'), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('ticker')
    )
    op.create_table('orders',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('user_id', sa.UUID(), nullable=False),
    sa.Column('status', sa.Enum('NEW', 'EXECUTED', 'CANCELLED', 'PARTIALLY_EXECUTED', name='statusorder'), nullable=False),
    sa.Column('direction', sa.Enum('BUY', 'SELL', name='direction'), nullable=False),
    sa.Column('qty', sa.Integer(), nullable=False),
    sa.Column('price', sa.Integer(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.Column('order_asset_id', sa.Integer(), nullable=False),
    sa.Column('payment_asset_id', sa.Integer(), nullable=False),
    sa.Column('filled', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['order_asset_id'], ['assets.id'], ),
    sa.ForeignKeyConstraint(['payment_asset_id'], ['assets.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('orders')
    op.drop_table('assets')
    # ### end Alembic commands ###
