from typing import Sequence

from alembic import op


revision: str = "0004"
down_revision: str | None = "0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        """
        ALTER TYPE public.lab_order_status
        ADD VALUE IF NOT EXISTS 'IN_PROGRESS' AFTER 'PLACED'
        """
    )
    op.execute(
        """
        ALTER TYPE public.lab_order_status
        ADD VALUE IF NOT EXISTS 'COMPLETED' AFTER 'IN_PROGRESS'
        """
    )
    op.execute(
        """
        ALTER TYPE public.lab_order_status
        ADD VALUE IF NOT EXISTS 'CANCELLED' AFTER 'COMPLETED'
        """
    )


def downgrade() -> None:
    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1
                FROM public.lab_orders
                WHERE status::text <> 'PLACED'
            ) THEN
                RAISE EXCEPTION
                    'Cannot downgrade lab_order_status while '
                    'non-PLACED lab orders exist';
            END IF;
        END
        $$;
        """
    )

    op.execute(
        """
        CREATE TYPE public.lab_order_status_0003
        AS ENUM ('PLACED')
        """
    )

    op.execute(
        """
        ALTER TABLE public.lab_orders
        ALTER COLUMN status
        TYPE public.lab_order_status_0003
        USING status::text::public.lab_order_status_0003
        """
    )

    op.execute(
        """
        DROP TYPE public.lab_order_status
        """
    )

    op.execute(
        """
        ALTER TYPE public.lab_order_status_0003
        RENAME TO lab_order_status
        """
    )
