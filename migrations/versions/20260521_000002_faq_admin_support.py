"""faq admin support

Revision ID: 20260521_000002
Revises: 20260414_000001
Create Date: 2026-05-21 10:00:00
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260521_000002"
down_revision = "20260414_000001"
branch_labels = None
depends_on = None


faq_table = sa.table(
    "faq_entries",
    sa.column("title", sa.String(length=255)),
    sa.column("keywords", sa.Text()),
    sa.column("content", sa.Text()),
    sa.column("sort_order", sa.Integer()),
    sa.column("is_active", sa.Boolean()),
)


def upgrade() -> None:
    op.create_table(
        "faq_entries",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("keywords", sa.Text(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("sort_order", sa.Integer(), server_default="0", nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_faq_entries_title"), "faq_entries", ["title"], unique=False)

    op.bulk_insert(
        faq_table,
        [
            {
                "title": "Адаптация в первые недели",
                "keywords": "адаптация,первокурсник,страшно,первая неделя,группа",
                "content": (
                    "В первые недели первокурснику важно узнать расписание, контакты куратора, "
                    "расположение деканата, правила пользования LMS и дедлайны по дисциплинам. "
                    "Полезно сразу вступить в чат группы и сохранить контакты старосты."
                ),
                "sort_order": 1,
                "is_active": True,
            },
            {
                "title": "Стипендия и выплаты",
                "keywords": "стипендия,выплаты,деньги,соцстипендия",
                "content": (
                    "Размер и условия стипендии зависят от университета. Обычно нужно уточнить "
                    "успеваемость, наличие задолженностей, форму обучения и основания для социальной поддержки."
                ),
                "sort_order": 2,
                "is_active": True,
            },
            {
                "title": "Общежитие",
                "keywords": "общежитие,заселение,комната,проживание",
                "content": (
                    "По общежитию чаще всего нужны документы, медицинские справки и приказ о заселении. "
                    "Стоит заранее уточнить сроки заселения, правила проживания, оплату и список нужных вещей."
                ),
                "sort_order": 3,
                "is_active": True,
            },
            {
                "title": "Общение с преподавателем",
                "keywords": "преподаватель,учитель,написать,письмо,уважительно",
                "content": (
                    "В сообщениях преподавателю лучше кратко представиться, указать группу, суть вопроса "
                    "и желаемое действие. Тон должен быть уважительным и деловым."
                ),
                "sort_order": 4,
                "is_active": True,
            },
            {
                "title": "Пропуски и отработки",
                "keywords": "пропуск,отработка,не был,болел,справка",
                "content": (
                    "Если есть пропуски, важно быстро уточнить правила отработки у преподавателя или куратора. "
                    "При болезни обычно нужна справка, а детали зависят от правил вуза."
                ),
                "sort_order": 5,
                "is_active": True,
            },
            {
                "title": "Экзамены и сессия",
                "keywords": "экзамен,сессия,зачет,подготовка",
                "content": (
                    "Перед сессией полезно собрать все дедлайны, уточнить формат контроля, критерии оценки "
                    "и список тем. Лучше вести календарь с датами зачетов, экзаменов и консультаций."
                ),
                "sort_order": 6,
                "is_active": True,
            },
        ],
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_faq_entries_title"), table_name="faq_entries")
    op.drop_table("faq_entries")
