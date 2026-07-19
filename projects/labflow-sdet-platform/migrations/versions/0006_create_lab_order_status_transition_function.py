from typing import Sequence

from alembic import op


revision: str = "0006"
down_revision: str | None = "0005"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        """
        CREATE FUNCTION public.transition_lab_order_status(
            p_lab_order_id uuid,
            p_requested_status public.lab_order_status
        )
        RETURNS public.lab_order_status
        LANGUAGE plpgsql
        VOLATILE
        AS $function$
        DECLARE
            v_current_status public.lab_order_status;
            v_resulting_status public.lab_order_status;
        BEGIN
            SELECT status
            INTO v_current_status
            FROM public.lab_orders
            WHERE id = p_lab_order_id
            FOR UPDATE;

            IF NOT FOUND THEN
                RAISE EXCEPTION
                    USING
                        ERRCODE = 'P0002',
                        MESSAGE = format(
                            'Lab order does not exist: %s',
                            p_lab_order_id
                        );
            END IF;

            IF NOT public.is_valid_lab_order_status_transition(
                v_current_status,
                p_requested_status
            ) THEN
                RAISE EXCEPTION
                    USING
                        ERRCODE = '23514',
                        MESSAGE = format(
                            'Invalid lab order status transition: '
                            '%s -> %s for lab order %s',
                            v_current_status,
                            p_requested_status,
                            p_lab_order_id
                        ),
                        CONSTRAINT = (
                            'ck_lab_order_status_transition'
                        );
            END IF;

            UPDATE public.lab_orders
            SET status = p_requested_status
            WHERE id = p_lab_order_id
            RETURNING status
            INTO v_resulting_status;

            RETURN v_resulting_status;
        END;
        $function$;
        """
    )


def downgrade() -> None:
    op.execute(
        """
        DROP FUNCTION IF EXISTS
            public.transition_lab_order_status(
                uuid,
                public.lab_order_status
            );
        """
    )
