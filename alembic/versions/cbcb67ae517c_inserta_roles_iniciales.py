"""inserta roles iniciales

Revision ID: cbcb67ae517c
Revises: d26118251188
Create Date: 2026-08-28 14:35:21.434770

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'cbcb67ae517c'
down_revision: Union[str, Sequence[str], None] = 'd26118251188'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(""" 
        INSERT INTO roles(name)
        VALUES
            ('director'),
            ('jefe_nacional'),
            ('coordinador'),
            ('analista'),
            ('auxiliar'),
            ('vendedor'),
            ('mercaimpulso')
    """)

def downgrade() -> None:
    op.execute("""
        DELETE FROM roles
        WHERE name IN (
            'director',
            'jefe_nacional',
            'coordinador',
            'analista',
            'auxiliar',
            'vendedor',
            'mercaimpulso'
        )
    """)
  
