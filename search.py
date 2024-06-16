import pandas as pd
import psycopg2
from psycopg2 import sql
from datetime import datetime


def calc_text_naturality(text, freq):
    save_text = text
    text = text.lower()
    metric = [freq.get(a+b, 0.2) for a, b in zip(text, text[1:]) if a.isalpha() and b.isalpha()]
    return (sum(metric) / len(metric)) ** 0.5, save_text


def translate_text(text, dict_):
    return ''.join(dict_.get(x, x) for x in text)


def find_lang(text, threshold=0.333):
    rus_key = "йцукенгшщзхъфывапролджэячсмитьбюЙЦУКЕНГШЩЗХЪФЫВАПРОЛДЖЭЯЧСМИТЬБЮ"
    eng_key = "qwertyuiop[]asdfghjkl;'zxcvbnm,.QWERTYUIOP[]ASDFGHJKL;'ZXCVBNM,."
    rus2eng = dict(zip(rus_key, eng_key))
    eng2rus = dict(zip(eng_key, rus_key))

    # русские биграммы
    # url_ru = 'https://docs.google.com/spreadsheets/d/1RRf5NIF1d0k9VonrByQXfUGu3tO41rYFu6gmg75IlSg/edit#gid=0'
    # df = pd.read_html(url_ru, index_col=0, encoding='UTF-8')[0]
    # df = df.iloc[:,:2]
    # df['C'] = df['B'] * len(df['B']) / df['B'].sum()
    # df.to_csv('ru_freq_2.csv', index=False)
    df = pd.read_csv('ru_freq_2.csv')
    freq_rus = dict(df[['A', 'C']].values)

    # английские биграммы
    # url_en = 'https://gist.githubusercontent.com/lydell/c439049abac2c9226e53/raw/4cfe39fd90d6ad25c4e683b6371009f574e1177f/bigrams.json'
    # df = pd.DataFrame(json.loads(requests.get(url_en).text), columns=['A','B'])
    # df = df.sort_values('B', ascending=False)[:100]
    # df['C'] = df['B'] * len(df['B']) / df['B'].sum()
    # df.to_csv('en_freq_2.csv', index=False)
    df = pd.read_csv('en_freq_2.csv')
    freq_eng = dict(df[['A', 'C']].values)

    trans_eng = translate_text(text, rus2eng)
    trans_rus = translate_text(text, eng2rus)
    scores = (calc_text_naturality(text, freq_eng),
              calc_text_naturality(text, freq_rus),
              calc_text_naturality(trans_eng, freq_eng),
              calc_text_naturality(trans_eng, freq_rus),
              calc_text_naturality(trans_rus, freq_eng),
              calc_text_naturality(trans_rus, freq_rus))
    max_score = max(scores)
    orig_score = max(scores[:2])
    return max_score[1] if (max_score[0] - threshold > orig_score[0]) else text


def preprocess_query(query, cursor):
    # Используем функцию `similarity` для нахождения похожих слов в таблице `tags`
    cursor.execute("""
    SELECT name FROM tags
    WHERE similarity(name, %s) > 0.3
    ORDER BY similarity(name, %s) DESC
    LIMIT 10;
    """, (query, query))

    similar_words = [row[0] for row in cursor.fetchall()]
    return ' | '.join(similar_words)


def search_videos(query, dbname, user, password, host, port, include_adult=True, max_duration=None, upload_date=None,
                  sort_by='relevance'):
    try:
        # Подключение к базе данных
        conn = psycopg2.connect(dbname=dbname, user=user, password=password, host=host, port=port)
        cursor = conn.cursor()

        # Предобработка запроса
        query = find_lang(query)
        preprocessed_query = preprocess_query(query, cursor)

        # Преобразование запроса в tsquery для обоих языков
        cursor.execute("SELECT to_tsquery('russian', %s) || to_tsquery('english', %s);",
                       (preprocessed_query, preprocessed_query))
        ts_query = cursor.fetchone()[0]

        # Базовый запрос
        base_query = sql.SQL("""
        SELECT link, ts_rank_cd(tags_tsvector, {ts_query}) AS rank
        FROM videos
        WHERE tags_tsvector @@ {ts_query}
        """).format(ts_query=sql.Literal(ts_query))

        # Добавление фильтров
        filters = []
        if not include_adult:
            filters.append(sql.SQL("adult = FALSE"))
        if max_duration is not None:
            filters.append(sql.SQL("duration <= {max_duration}").format(max_duration=sql.Literal(max_duration)))
        if upload_date is not None:
            filters.append(sql.SQL("date >= {upload_date}").format(upload_date=sql.Literal(upload_date)))

        if filters:
            base_query += sql.SQL(" AND ") + sql.SQL(" AND ").join(filters)

        # Добавление сортировки
        if sort_by == 'views':
            order_clause = sql.SQL(" ORDER BY views DESC, rank DESC")
        elif sort_by == 'date':
            order_clause = sql.SQL(" ORDER BY date DESC, rank DESC")
        else:
            order_clause = sql.SQL(" ORDER BY rank DESC")

        final_query = base_query + order_clause

        # Выполнение поиска
        cursor.execute(final_query)

        # Извлечение результатов
        links = [row[0] for row in cursor.fetchall()]

        return links

    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        cursor.close()
        conn.close()


if __name__ == '__main__':
    dbname = 'postgres'
    user = 'searcher'
    password = '789'
    host = 'localhost'
    port = '5432'
    query = 'бар'

    # Example of using the function with filters and sorting
    results = search_videos(query, dbname, user, password, host, port,
                            include_adult=True)
    print(results)
