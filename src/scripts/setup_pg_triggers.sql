-- Create change_log table
CREATE TABLE IF NOT EXISTS change_log (
    id SERIAL PRIMARY KEY,
    table_name VARCHAR,
    operation VARCHAR,
    record_id INTEGER,
    new_data JSONB,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create trigger function
CREATE OR REPLACE FUNCTION notify_change()
RETURNS TRIGGER AS $$
DECLARE
    record_id INTEGER;
    new_data JSONB;
BEGIN
    IF TG_OP = 'INSERT' OR TG_OP = 'UPDATE' THEN
        record_id := NEW.id;
        new_data := row_to_json(NEW)::JSONB;
    ELSE
        record_id := OLD.id;
        new_data := NULL;
    END IF;
    INSERT INTO change_log (table_name, operation, record_id, new_data)
    VALUES (TG_TABLE_NAME, TG_OP, record_id, new_data);
    PERFORM pg_notify('table_change', TG_TABLE_NAME || ':' || TG_OP || ':' || record_id::TEXT);
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

-- Drop and create trigger for job_interactions
DROP TRIGGER IF EXISTS job_interactions_change_trigger ON job_interactions;
CREATE TRIGGER job_interactions_change_trigger
AFTER INSERT OR UPDATE OR DELETE ON job_interactions
FOR EACH ROW EXECUTE FUNCTION notify_change();

-- Drop and create trigger for job_actions
DROP TRIGGER IF EXISTS job_actions_change_trigger ON job_actions;
CREATE TRIGGER job_actions_change_trigger
AFTER INSERT OR UPDATE OR DELETE ON job_actions
FOR EACH ROW EXECUTE FUNCTION notify_change();