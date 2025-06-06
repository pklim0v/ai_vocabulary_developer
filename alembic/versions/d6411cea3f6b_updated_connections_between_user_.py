"""Updated connections between User, UserAgreement and PrivacyPolicy

Revision ID: d6411cea3f6b
Revises: 0b470c3d561a
Create Date: 2025-05-31 01:47:30.643602

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd6411cea3f6b'
down_revision: Union[str, None] = '0b470c3d561a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.add_column(sa.Column('accepted_agreement_id', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('accepted_privacy_policy_id', sa.Integer(), nullable=True))
        batch_op.create_foreign_key(
            'fk_users_accepted_agreement_id',
            'user_agreements',
            ['accepted_agreement_id'],
            ['id']
        )
        batch_op.create_foreign_key(
            'fk_users_accepted_privacy_policy_id',
            'privacy_policies',
            ['accepted_privacy_policy_id'],
            ['id']
        )

    # ### end Alembic commands ###


def downgrade() -> None:
    """Downgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.drop_constraint('fk_users_accepted_agreement_id', type_='foreignkey')
        batch_op.drop_constraint('fk_users_accepted_privacy_policy_id', type_='foreignkey')
        batch_op.drop_column('accepted_privacy_policy_id')
        batch_op.drop_column('accepted_agreement_id')

    # ### end Alembic commands ###