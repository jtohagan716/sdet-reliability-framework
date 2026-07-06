CREATE INDEX IF NOT EXISTS idx_encounters_completed_patient_date
ON encounters (patient_id, encounter_date DESC)
WHERE status = 'completed';
