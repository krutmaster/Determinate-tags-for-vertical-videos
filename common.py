from keybert import KeyBERT
import pymorphy3
from better_profanity import profanity
import csv
from deep_translator import GoogleTranslator


def generate_hashtags(descriptions, n_words=6):
    # Инициализация модели KeyBERT
    model = KeyBERT('distilbert-base-nli-mean-tokens')

    hashtags = []
    # Извлечение ключевых слов
    for text in descriptions:
        keywords = model.extract_keywords(text, top_n=n_words)

        # Преобразование ключевых слов в хештеги
        hashtag = [str(keyword[0]) for keyword in keywords]
        hashtags.append(hashtag)

    return hashtags


def load_custom_bad_words(csv_file):
    with open(csv_file, 'r', encoding='utf-8') as infile:
        reader = csv.reader(infile)
        next(reader)  # Пропускаем заголовок
        custom_bad_words = [row[0] for row in reader]
    return custom_bad_words


def lemmatize_text(text):
    """
    Функция для лемматизации текста
    Преобразуем каждое слово в его базовую форму перед проверкой
    """
    morph = pymorphy3.MorphAnalyzer()  # Создаем анализатор для лемматизации

    words = text.split()
    lemmatized_words = [morph.parse(word)[0].normal_form for word in words]
    return ' '.join(lemmatized_words)


def contains_profanity(text):
    """
    Функция для проверки мата с учетом лемматизации
    Возвращает True если есть мат и False если нет
    """
    custom_bad_words = load_custom_bad_words('custom_ru_bad_words.csv')
    profanity.load_censor_words(custom_bad_words)
    lemmatized_text = lemmatize_text(text)
    return profanity.contains_profanity(lemmatized_text)


def add_bad_words(csv_file, english_bad_words):
    # Читаем существующие слова из CSV файла
    existing_bad_words = set()
    with open(csv_file, 'r', encoding='utf-8') as infile:
        reader = csv.reader(infile)
        next(reader)  # Пропускаем заголовок
        for row in reader:
            existing_bad_words.add(row[0])

    # Добавляем новые слова, избегая дубликатов
    with open(csv_file, 'a', newline='', encoding='utf-8') as outfile:
        writer = csv.writer(outfile)
        for word in english_bad_words:
            if word not in existing_bad_words:
                writer.writerow([word])


def translate_text(text, target_language='en'):
    """
    Переводит текст на указанный язык (по умолчанию на русский)
    """
    if isinstance(text, str):
        translated = GoogleTranslator(source='auto', target=target_language).translate(text)
        return translated
    translated = [GoogleTranslator(source='auto', target=target_language).translate(word) for word in text if len(word.split()) > 0]
    return translated


# def detect_language(text):
#     """
#     Определяет язык заданного текста
#     Если возникает ошибка возвращает 'ru'
#     """
#     try:
#         lang = single_detection(text, api="google")
#         return lang
#     except:
#         return 'ru'


if __name__ == '__main__':
    text = 'тестирование переводчика'
    print(translate_text(text))
    print(translate_text(text, 'ru'))
