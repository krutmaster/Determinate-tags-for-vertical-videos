from common import generate_hashtags, translate_text
from transformers import BlipProcessor, BlipForConditionalGeneration
import torch
from torchvision import models, transforms
import requests
import json
import os
import numpy as np
import cv2
from collections import Counter


def description_video_action(frame):
  # Загрузка модели
  processor = BlipProcessor.from_pretrained("Salesforce/blip-image-captioning-base")
  model = BlipForConditionalGeneration.from_pretrained("Salesforce/blip-image-captioning-base")

  # преобразование входных данных
  inputs = processor(frame, return_tensors="pt")

  # Генерация описания изображения
  output = model.generate(**inputs)

  # Декодирование и вывод описания
  description = processor.decode(output[0], skip_special_tokens=True)
  return description


LABELS_FILE = 'imagenet_labels.json'


# Функция для загрузки меток классов и сохранения их в файл
def download_labels(url: str, file_path: str):
    if not os.path.exists(file_path):
        response = requests.get(url)
        labels = response.json()
        with open(file_path, 'w') as f:
            json.dump(labels, f)
    else:
        with open(file_path, 'r') as f:
            labels = json.load(f)
    return labels


# Загрузка предварительно обученной модели
model = models.resnet50(pretrained=True)
model.eval()

# Определение трансформаций для предобработки изображения
preprocess = transforms.Compose([
    transforms.ToPILImage(),
    transforms.Resize(256),
    transforms.CenterCrop(224),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
])


# Функция для предсказания жанра изображения
def predict_image_genre(frame: np.ndarray, labels: list) -> str:
    # Преобразование кадра из формата numpy.ndarray в нужный формат
    image = preprocess(frame)
    image = image.unsqueeze(0)

    # Прогон через модель
    with torch.no_grad():
        outputs = model(image)

    # Получение предсказанного класса
    _, predicted_idx = torch.max(outputs, 1)
    predicted_label = labels[predicted_idx.item()]

    return predicted_label


# Функция для определения наиболее частого жанра
def determine_genre(frames) -> str:
    LABELS_URL = "https://raw.githubusercontent.com/anishathalye/imagenet-simple-labels/master/imagenet-simple-labels.json"
    labels = download_labels(LABELS_URL, LABELS_FILE)

    # frames = extract_frames(video_path) Для тестирование без связи с остальной частью
    genres = [predict_image_genre(frame, labels) for frame in frames]

    most_common_genre = Counter(genres).most_common(1)[0][0]
    return most_common_genre


def tags_from_video(frames, max_frames=18):
    descriptions = set()
    for frame in frames:
        words_description = set(description_video_action(frame).split())
        description = ' '.join(str(word) for word in words_description)
        descriptions.add(description)
    genre = determine_genre(frames)
    entags = generate_hashtags(translate_text(descriptions))[0]
    entags.append(genre)
    rutags = translate_text(entags, 'ru')
    return rutags, entags
