from typing import Sequence

from alembic import op


revision: str = "0007"
down_revision: str | None = "0006"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE public.lab_order_status_audit (
            id bigint GENERATED ALWAYS AS IDENTITY,
            lab_order_id uuid NOT NULL,
            previous_status public.lab_order_status NOT NULL,
            new_status public.lab_order_status NOT NULL,
            changed_by text NOT NULL,
            application_name text NOT NULL,
            changed_at timestamp with time zone NOT NULL
                DEFAULT clock_timestamp(),

            CONSTRAINT pk_lab_order_status_audit
                PRIMARY KEY (id),

            CONSTRAINT fk_lab_order_status_audit_lab_order
                FOREIGN KEY (lab_order_id)
                REFERENCES public.lab_orders (id)
                ON DELETE CASCADE,

            CONSTRAINT ck_lab_order_status_audit_changed
                CHECK (previous_status IS DISTINCT FROM new_status)
        );
        """
    )

    op.execute(
        """
        CREATE INDEX ix_lab_order_status_audit_order_id
        ON public.lab_order_status_audit (
            lab_order_id,
            id
        );
        """
    )

    op.execute(
        """
        CREATE FUNCTION public.audit_lab_order_status_change()
        RETURNS trigger
        LANGUAGE plpgsql
        VOLATILE
        AS $function$
        BEGIN
            INSERT INTO public.lab_order_status_audit (
                lab_order_id,
                previous_status,
                new_status,
                changed_by,
                application_name,
                changed_at
            )
            VALUES (
                NEW.id,
                OLD.status,
                NEW.status,
                current_user,
                current_setting(
                    'application_name',
                    true
                ),
                clock_timestamp()
            );

            RETURN NEW;
        END;
        $function$;
        """
    )

    op.execute(
        """
        CREATE TRIGGER trg_lab_orders_status_audit
        AFTER UPDATE OF status
        ON public.lab_orders
        FOR EACH ROW
        WHEN (
            OLD.status IS DISTINCT FROM NEW.status
        )
        EXECUTE FUNCTION
            public.audit_lab_order_status_change();
        """
    )


def downgrade() -> None:
    op.execute(
        """
        DROP TRIGGER IF EXISTS
            trg_lab_orders_status_audit
        ON public.lab_orders;
        """
    )

    op.execute(
        """
        DROP FUNCTION IF EXISTS
            public.audit_lab_order_status_change();
        """
    )

    op.execute(
        """
        DROP TABLE IF EXISTS
            public.lab_order_status_audit;
        """
    )
