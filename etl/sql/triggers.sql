CREATE OR REPLACE FUNCTION notify_table_change()
RETURNS TRIGGER AS $$
DECLARE
    payload JSON;
BEGIN
    IF (TG_OP = 'DELETE') THEN
        payload = json_build_object(
            'table', TG_TABLE_NAME,
            'id', OLD.id,
            'operation', TG_OP
        );
    ELSE
        payload = json_build_object(
            'table', TG_TABLE_NAME,
            'id', NEW.id,
            'operation', TG_OP
        );
    END IF;

    PERFORM pg_notify('content_changes', payload::text);
    RETURN COALESCE(NEW, OLD);
END;
$$ LANGUAGE plpgsql;

-- Триггеры на изменение таблиц
DROP TRIGGER IF EXISTS film_work_change ON content.film_work;
CREATE TRIGGER film_work_change
AFTER INSERT OR UPDATE OR DELETE ON content.film_work
FOR EACH ROW EXECUTE FUNCTION notify_table_change();

DROP TRIGGER IF EXISTS genre_change ON content.genre;
CREATE TRIGGER genre_change
AFTER INSERT OR UPDATE OR DELETE ON content.genre
FOR EACH ROW EXECUTE FUNCTION notify_table_change();

DROP TRIGGER IF EXISTS person_change ON content.person;
CREATE TRIGGER person_change
AFTER INSERT OR UPDATE OR DELETE ON content.person
FOR EACH ROW EXECUTE FUNCTION notify_table_change();

DROP TRIGGER IF EXISTS genre_film_work_change ON content.genre_film_work;

CREATE TRIGGER genre_film_work_change
AFTER INSERT OR UPDATE OR DELETE ON content.genre_film_work
FOR EACH ROW EXECUTE FUNCTION notify_table_change();

DROP TRIGGER IF EXISTS person_film_work_change ON content.person_film_work;

CREATE TRIGGER person_film_work_change
AFTER INSERT OR UPDATE OR DELETE ON content.person_film_work
FOR EACH ROW EXECUTE FUNCTION notify_table_change();