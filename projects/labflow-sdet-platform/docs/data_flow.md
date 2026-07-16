# Laboratory Order Data Flow — v0.1

## Input fields

- `placer_order_number`
- `synthetic_patient_id`
- `test_code`
- `priority`
- `ordered_at`

## Generated fields

- `id`
- `status`
- `created_at`

## Persistence

All order data is written to `lab_orders`.

## Limitation

No specimen, accession, result, queue, cache, or interface records exist yet.
