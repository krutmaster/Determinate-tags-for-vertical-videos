import psycopg2


def create_database_and_tables(dbname, dbuser, dbpassword, host='localhost', port='5432'):
    try:
        conn = psycopg2.connect(dbname=dbname, user=dbuser, password=dbpassword, host=host, port=port)
        conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()

        # Создаем таблицу videos
        cursor.execute("""
        CREATE TABLE videos (
            id SERIAL PRIMARY KEY,
            link TEXT NOT NULL,
            date TIMESTAMP NOT NULL DEFAULT now(),
            duration INTEGER NOT NULL,
            description TEXT,
            views INTEGER NOT NULL DEFAULT 0,
            adult BOOLEAN NOT NULL,
            tags_tsvector TSVECTOR
        );
        """)

        # Создаем таблицу tags
        cursor.execute("""
        CREATE TABLE tags (
            id SERIAL PRIMARY KEY,
            name TEXT NOT NULL UNIQUE
        );
        """)

        # Создаем таблицу video_tags
        cursor.execute("""
        CREATE TABLE video_tags (
            video_id INTEGER REFERENCES videos(id),
            tag_id INTEGER REFERENCES tags(id),
            PRIMARY KEY (video_id, tag_id)
        );
        """)

        # Создаем пользователей uploader и searcher
        cursor.execute("CREATE USER uploader WITH ENCRYPTED PASSWORD 'uploader_password';")
        cursor.execute("CREATE USER searcher WITH ENCRYPTED PASSWORD 'searcher_password';")
        print("Users uploader and searcher created successfully.")

        # Назначаем права доступа
        cursor.execute("GRANT SELECT, INSERT, UPDATE, DELETE ON videos TO uploader;")
        cursor.execute("GRANT SELECT, INSERT, UPDATE, DELETE ON tags TO uploader;")
        cursor.execute("GRANT SELECT, INSERT, UPDATE, DELETE ON video_tags TO uploader;")
        cursor.execute("GRANT SELECT ON videos TO searcher;")
        cursor.execute("GRANT SELECT ON tags TO searcher;")
        cursor.execute("GRANT SELECT ON video_tags TO searcher;")

        # Предоставляем права доступа к последовательностям
        cursor.execute("GRANT USAGE, SELECT ON SEQUENCE videos_id_seq TO uploader;")
        cursor.execute("GRANT USAGE, SELECT ON SEQUENCE tags_id_seq TO uploader;")

        print("Permissions granted successfully.")

        # Добавляем tsvector столбец
        cursor.execute("ALTER TABLE videos ADD COLUMN tags_tsvector tsvector;")

        # Создаем функцию для обновления tsvector
        cursor.execute("""
        CREATE OR REPLACE FUNCTION update_tags_tsvector() RETURNS TRIGGER AS $$
        BEGIN
            UPDATE videos
            SET tags_tsvector = to_tsvector(
                'russian',
                (SELECT string_agg(t.name, ' ')
                 FROM video_tags vt
                 JOIN tags t ON vt.tag_id = t.id
                 WHERE vt.video_id = NEW.video_id))
            WHERE id = NEW.video_id;

            RETURN NULL;
        END;
        $$ LANGUAGE plpgsql;
        """)

        # Создаем триггер для обновления tsvector
        cursor.execute("""
        CREATE TRIGGER trigger_update_video_tags_tsvector
        AFTER INSERT OR DELETE ON video_tags
        FOR EACH ROW EXECUTE FUNCTION update_tags_tsvector();
        """)

        # Подключаем расширение pg_trgm, если оно еще не подключено
        cursor.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm;")

    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        cursor.close()
        conn.close()


def add_video_with_tags(dbname, user, password, host, port, video_link, duration, description, adult, ru_tags, en_tags):
    try:
        # Подключаемся к базе данных
        conn = psycopg2.connect(dbname=dbname, user=user, password=password, host=host, port=port)
        cursor = conn.cursor()

        # Добавляем ссылку на видео в таблицу videos
        cursor.execute("INSERT INTO videos (link, duration, description, adult) VALUES (%s, %s, %s, %s) RETURNING id;", (video_link, duration, description, adult,))
        video_id = cursor.fetchone()[0]

        # Объединяем русские и английские теги в один набор для обработки
        all_tags = ru_tags.union(en_tags)

        # Добавляем теги и связи в таблицу video_tags
        for tag in all_tags:
            cursor.execute("SELECT id FROM tags WHERE name = %s;", (tag,))
            result = cursor.fetchone()

            if result:
                tag_id = result[0]
            else:
                cursor.execute("INSERT INTO tags (name) VALUES (%s) RETURNING id;", (tag,))
                tag_id = cursor.fetchone()[0]

            cursor.execute("INSERT INTO video_tags (video_id, tag_id) VALUES (%s, %s);", (video_id, tag_id))

        # Сохраняем изменения в базе данных
        conn.commit()

        print("Video and tags added successfully.")

    except Exception as e:
        print(f"An error occurred: {e}")
        if conn:
            conn.rollback()
    finally:
        cursor.close()
        conn.close()
