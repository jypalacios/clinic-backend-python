-- Edad de pacientes: requiere pg_cron instalado y habilitado mediante
-- shared_preload_libraries. Configure cron.database_name con la base de datos
-- de la clínica y cron.timezone = 'America/Bogota' en postgresql.conf.

ALTER TABLE patients
    ADD COLUMN IF NOT EXISTS edad INTEGER;

UPDATE patients
SET edad = EXTRACT(
    YEAR FROM age((CURRENT_TIMESTAMP AT TIME ZONE 'America/Bogota')::DATE, fec_nacimiento)
)::INTEGER
WHERE edad IS DISTINCT FROM
      EXTRACT(
          YEAR FROM age((CURRENT_TIMESTAMP AT TIME ZONE 'America/Bogota')::DATE, fec_nacimiento)
      )::INTEGER;

ALTER TABLE patients
    ALTER COLUMN edad SET NOT NULL;

CREATE OR REPLACE FUNCTION actualizar_edad_paciente()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    NEW.edad := EXTRACT(
        YEAR FROM age((CURRENT_TIMESTAMP AT TIME ZONE 'America/Bogota')::DATE, NEW.fec_nacimiento)
    )::INTEGER;
    RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS trg_actualizar_edad_paciente ON patients;

CREATE TRIGGER trg_actualizar_edad_paciente
    BEFORE INSERT OR UPDATE OF fec_nacimiento, edad
    ON patients
    FOR EACH ROW
    EXECUTE FUNCTION actualizar_edad_paciente();

CREATE EXTENSION IF NOT EXISTS pg_cron;

SELECT cron.schedule(
    'actualizar-edad-pacientes',
    '0 1 * * *',
    $job$
        UPDATE patients
        SET edad = EXTRACT(
            YEAR FROM age((CURRENT_TIMESTAMP AT TIME ZONE 'America/Bogota')::DATE, fec_nacimiento)
        )::INTEGER
        WHERE edad IS DISTINCT FROM
              EXTRACT(
                  YEAR FROM age((CURRENT_TIMESTAMP AT TIME ZONE 'America/Bogota')::DATE, fec_nacimiento)
              )::INTEGER;
    $job$
);
