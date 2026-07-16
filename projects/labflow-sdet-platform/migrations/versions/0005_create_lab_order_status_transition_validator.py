from typing import Sequence

from alembic import op


revision: str = "0005"
down_revision: str | None = "0004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        """
        CREATE FUNCTION
            public.is_valid_lab_order_status_transition(
                current_status public.lab_order_status,
                requested_status public.lab_order_status
            )
        RETURNS boolean
        LANGUAGE sql
        IMMUTABLE
        PARALLEL SAFE
        AS $function$
            SELECT
                (
                    current_status = 'PLACED'
                    AND requested_status IN (
                        'IN_PROGRESS',
                        'CANCELLED'
                    )
                )
                OR
                (
                    current_status = 'IN_PROGRESS'
                    AND requested_status IN (
                        'COMPLETED',
                        'CANCELLED'
                    )
                );
        $function$;
        """
    )


def downgrade() -> None:
    op.execute(
        """
        DROP FUNCTION IF EXISTS
            public.is_valid_lab_order_status_transition(
                public.lab_order_status,
                public.lab_order_status
            );
        """
    )
