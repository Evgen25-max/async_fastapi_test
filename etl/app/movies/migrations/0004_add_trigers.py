# movies/migrations/0002_add_triggers.py

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('movies', '0003_filmwork_idx_film_work_modified_id_and_more'),
    ]

    operations = [
        migrations.RunSQL(
            sql="""

            CREATE OR REPLACE FUNCTION content.update_films_modified(film_ids uuid[])
            RETURNS void AS $$
            BEGIN
                UPDATE content.film_work
                SET modified = CLOCK_TIMESTAMP()
                WHERE id = ANY(film_ids);
            END;
            $$ LANGUAGE plpgsql;

            CREATE OR REPLACE FUNCTION content.on_person_delete()
            RETURNS TRIGGER AS $$
            BEGIN
                PERFORM content.update_films_modified(
                    ARRAY(SELECT film_work_id FROM content.person_film_work WHERE person_id = OLD.id)
                );
                RETURN OLD;
            END;
            $$ LANGUAGE plpgsql;

            CREATE OR REPLACE FUNCTION content.on_genre_delete()
            RETURNS TRIGGER AS $$
            BEGIN
                PERFORM content.update_films_modified(
                    ARRAY(SELECT film_work_id FROM content.genre_film_work WHERE genre_id = OLD.id)
                );
                RETURN OLD;
            END;
            $$ LANGUAGE plpgsql;

            CREATE OR REPLACE FUNCTION content.on_person_film_work_change()
            RETURNS TRIGGER AS $$
            BEGIN
                IF TG_OP = 'INSERT' THEN
                    UPDATE content.film_work
                    SET modified = CLOCK_TIMESTAMP()
                    WHERE id = NEW.film_work_id;
                ELSIF TG_OP = 'DELETE' THEN
                    UPDATE content.film_work
                    SET modified = CLOCK_TIMESTAMP()
                    WHERE id = OLD.film_work_id;
                ELSIF TG_OP = 'UPDATE' THEN
                    UPDATE content.film_work
                    SET modified = CLOCK_TIMESTAMP()
                    WHERE id IN (OLD.film_work_id, NEW.film_work_id);
                END IF;

                RETURN NULL;
            END;
            $$ LANGUAGE plpgsql;

            CREATE OR REPLACE FUNCTION content.on_genre_film_work_change()
            RETURNS TRIGGER AS $$
            BEGIN
                IF TG_OP = 'INSERT' THEN
                    UPDATE content.film_work
                    SET modified = CLOCK_TIMESTAMP()
                    WHERE id = NEW.film_work_id;
                ELSIF TG_OP = 'DELETE' THEN
                    UPDATE content.film_work
                    SET modified = CLOCK_TIMESTAMP()
                    WHERE id = OLD.film_work_id;
                ELSIF TG_OP = 'UPDATE' THEN
                    UPDATE content.film_work
                    SET modified = CLOCK_TIMESTAMP()
                    WHERE id IN (OLD.film_work_id, NEW.film_work_id);
                END IF;

                RETURN NULL;
            END;
            $$ LANGUAGE plpgsql;

            CREATE OR REPLACE FUNCTION content.set_film_work_modified()
            RETURNS TRIGGER AS $$
            BEGIN
                NEW.modified := CLOCK_TIMESTAMP();
                RETURN NEW;
            END;
            $$ LANGUAGE plpgsql;


            CREATE TRIGGER trg_person_delete
            BEFORE DELETE ON content.person
            FOR EACH ROW
            EXECUTE FUNCTION content.on_person_delete();

            CREATE TRIGGER trg_genre_delete
            BEFORE DELETE ON content.genre
            FOR EACH ROW
            EXECUTE FUNCTION content.on_genre_delete();

            CREATE TRIGGER trg_pfw_insert
            AFTER INSERT ON content.person_film_work
            FOR EACH ROW EXECUTE FUNCTION content.on_person_film_work_change();

            CREATE TRIGGER trg_pfw_delete
            AFTER DELETE ON content.person_film_work
            FOR EACH ROW EXECUTE FUNCTION content.on_person_film_work_change();

            CREATE TRIGGER trg_pfw_update
            AFTER UPDATE ON content.person_film_work
            FOR EACH ROW EXECUTE FUNCTION content.on_person_film_work_change();

            CREATE TRIGGER trg_gfw_insert
            AFTER INSERT ON content.genre_film_work
            FOR EACH ROW EXECUTE FUNCTION content.on_genre_film_work_change();

            CREATE TRIGGER trg_gfw_delete
            AFTER DELETE ON content.genre_film_work
            FOR EACH ROW EXECUTE FUNCTION content.on_genre_film_work_change();

            CREATE TRIGGER trg_gfw_update
            AFTER UPDATE ON content.genre_film_work
            FOR EACH ROW EXECUTE FUNCTION content.on_genre_film_work_change();

            CREATE TRIGGER trg_film_work_modified
            BEFORE UPDATE ON content.film_work
            FOR EACH ROW
            WHEN (OLD.* IS DISTINCT FROM NEW.*)
            EXECUTE FUNCTION content.set_film_work_modified();
            """,
            reverse_sql="""
            -- Удаляем триггеры (сначала триггеры, потом функции!)
            DROP TRIGGER IF EXISTS trg_film_work_modified ON content.film_work;
            DROP TRIGGER IF EXISTS trg_gfw_update ON content.genre_film_work;
            DROP TRIGGER IF EXISTS trg_gfw_delete ON content.genre_film_work;
            DROP TRIGGER IF EXISTS trg_gfw_insert ON content.genre_film_work;
            DROP TRIGGER IF EXISTS trg_pfw_update ON content.person_film_work;
            DROP TRIGGER IF EXISTS trg_pfw_delete ON content.person_film_work;
            DROP TRIGGER IF EXISTS trg_pfw_insert ON content.person_film_work;
            DROP TRIGGER IF EXISTS trg_genre_delete ON content.genre;
            DROP TRIGGER IF EXISTS trg_person_delete ON content.person;

            -- Удаляем функции
            DROP FUNCTION IF EXISTS content.set_film_work_modified();
            DROP FUNCTION IF EXISTS content.on_genre_film_work_change();
            DROP FUNCTION IF EXISTS content.on_person_film_work_change();
            DROP FUNCTION IF EXISTS content.on_genre_delete();
            DROP FUNCTION IF EXISTS content.on_person_delete();
            DROP FUNCTION IF EXISTS content.update_films_modified(uuid[]);
            """
        ),
    ]
