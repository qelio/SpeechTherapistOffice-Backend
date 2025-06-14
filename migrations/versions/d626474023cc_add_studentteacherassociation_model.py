"""Add StudentTeacherAssociation model

Revision ID: d626474023cc
Revises: 6d8923093daf
Create Date: 2025-06-13 15:15:30.844463

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'd626474023cc'
down_revision = '6d8923093daf'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('Students_has_Teachers',
    sa.Column('student_user_id', sa.Integer(), nullable=False),
    sa.Column('teacher_user_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['student_user_id'], ['Students.user_id'], name=op.f('fk_Students_has_Teachers_student_user_id_Students')),
    sa.ForeignKeyConstraint(['teacher_user_id'], ['Teachers.user_id'], name=op.f('fk_Students_has_Teachers_teacher_user_id_Teachers')),
    sa.PrimaryKeyConstraint('student_user_id', 'teacher_user_id', name=op.f('pk_Students_has_Teachers'))
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('Students_has_Teachers')
    # ### end Alembic commands ###
