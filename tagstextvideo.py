from common import generate_hashtags, contains_profanity, translate_text
import numpy as np
import pytesseract
from pytesseract import Output
import cv2
import re


# Заменить путь до файла на свой или закинуть его в PATH
pytesseract.pytesseract.tesseract_cmd = r'C:\Users\krutm\AppData\Local\Programs\Tesseract-OCR\tesseract.exe'


def image_to_text(image):
    text = ''
    # image = cv2.imread(image_path)

    # Преобразование изображения в оттенки серого
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # Применение двоичного порогового преобразования
    _, binary = cv2.threshold(gray, 180, 255, cv2.THRESH_BINARY_INV)
    tesseract_config = r'--oem 3 --psm 6 -l rus+eng'
    # Используем pytesseract для извлечения данных о блоках текста
    data = pytesseract.image_to_data(binary, config=tesseract_config, output_type=pytesseract.Output.DICT)

    n_boxes = len(data['level'])
    for i in range(n_boxes):
        # Извлекаем координаты и размер блока
        (x, y, w, h) = (data['left'][i], data['top'][i], data['width'][i], data['height'][i])

        # Извлекаем текст из блока
        photo_text = data['text'][i]

        # Извлекаем значение уверенности (confidence)
        conf = float(data['conf'][i])

        # Проверка, что текст не пустой, значение уверенности выше порога и текст не состоит только из специальных символов
        if photo_text.strip() and conf > 60 and re.search(r'\w', photo_text):
            text += photo_text + ' '
    return (text)


def tags_from_text(frames):
    descriptions = set()
    for frame in frames:
        text = image_to_text(frame)
        descriptions.add(text)
    entags = generate_hashtags(translate_text(descriptions))
    adult = contains_profanity(' '.join(str(word) for word in descriptions))
    rutags = translate_text(entags, 'ru')
    return rutags, entags, adult
