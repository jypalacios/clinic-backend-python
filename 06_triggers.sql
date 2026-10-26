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

-- ---------------------------------------------------------------------
-- Cierre diario de citas del día anterior (01:00, zona America/Bogota)
--   PROGRAMADA / CONFIRMADA -> NO_ASISTIO
--   EN SALA DE ESPERA       -> ATENDIDA
-- ---------------------------------------------------------------------
CREATE OR REPLACE FUNCTION cerrar_citas_dia_anterior()
RETURNS INTEGER
LANGUAGE plpgsql
AS $$
DECLARE
    v_programada  INTEGER;
    v_confirmada  INTEGER;
    v_sala        INTEGER;
    v_no_asistio  INTEGER;
    v_atendida    INTEGER;
    v_inicio      TIMESTAMPTZ;
    v_fin         TIMESTAMPTZ;
    v_total       INTEGER;
BEGIN
    SELECT id_estado INTO STRICT v_programada FROM estados WHERE proceso = 'citas' AND nom_estado = 'PROGRAMADA';
    SELECT id_estado INTO STRICT v_confirmada FROM estados WHERE proceso = 'citas' AND nom_estado = 'CONFIRMADA';
    SELECT id_estado INTO STRICT v_sala       FROM estados WHERE proceso = 'citas' AND nom_estado = 'EN SALA DE ESPERA';
    SELECT id_estado INTO STRICT v_no_asistio FROM estados WHERE proceso = 'citas' AND nom_estado = 'NO_ASISTIO';
    SELECT id_estado INTO STRICT v_atendida   FROM estados WHERE proceso = 'citas' AND nom_estado = 'ATENDIDA';

    v_fin    := date_trunc('day', now() AT TIME ZONE 'America/Bogota') AT TIME ZONE 'America/Bogota';
    v_inicio := v_fin - INTERVAL '1 day';

    UPDATE appointments
    SET id_estado = CASE
                        WHEN id_estado = v_sala THEN v_atendida
                        ELSE v_no_asistio
                    END,
        fec_actualizacion = now()
    WHERE fecha_hora >= v_inicio
      AND fecha_hora <  v_fin
      AND id_estado IN (v_programada, v_confirmada, v_sala);

    GET DIAGNOSTICS v_total = ROW_COUNT;
    RETURN v_total;
END;
$$;

SELECT cron.schedule(
    'cerrar-citas-dia-anterior',
    '0 1 * * *',
    $job$ SELECT cerrar_citas_dia_anterior(); $job$
);
