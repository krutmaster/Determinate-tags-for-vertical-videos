import os.path

from common import generate_hashtags, translate_text, contains_profanity
import speech_recognition as sr
from pydub import AudioSegment
import whisper
import tensorflow as tf
import tensorflow_hub as hub
import numpy as np
import soundfile as sf
import librosa
import csv
import requests
import ffmpeg


def extract_audio_to_wav(video_path, output_wav_path='audio.wav'):
    """
    Extracts audio from a video file and converts it to WAV format.
    Saves the audio data to the specified output file and returns the output file path.

    :param video_path: Path to the video file
    :param output_wav_path: Path to the output WAV file
    :return: Path to the saved WAV file
    """
    # Run ffmpeg to extract audio and convert to WAV, then save to file
    if os.path.exists('audio.wav'):
        os.remove('audio.wav')
    (
        ffmpeg
        .input(video_path)
        .output(output_wav_path, format='wav')
        .run()
    )

    return output_wav_path


def language_detect(audio_path):
    """
    Функция для определения языка аудио.
    На вход путь до файла, на выходе язык.
    """
    model_name = 'base'  # можно заменить на large для большей точности, но дольше работает
    model = whisper.load_model(model_name)

    audio = whisper.load_audio(audio_path)
    audio = whisper.pad_or_trim(audio)

    mel = whisper.log_mel_spectrogram(audio).to(model.device)

    _, probs = model.detect_language(mel)
    return max(probs, key=probs.get)


def convert_audio_to_text(audio_file, lang):
    """
    Google Web Speech API для распознавания речи
    В recognize_google можно указать язык (параметр language)
    """
    recognizer = sr.Recognizer()
    audio = AudioSegment.from_file(audio_file)
    audio.export("temp.wav", format="wav")
    with sr.AudioFile("temp.wav") as source:
        audio_data = recognizer.record(source)
        text = recognizer.recognize_google(audio_data, language=lang) # Выбор языка
        return text


def download_yamnet_class_map():
    url = "https://raw.githubusercontent.com/tensorflow/models/master/research/audioset/yamnet/yamnet_class_map.csv"
    response = requests.get(url)
    class_map = []
    if response.status_code == 200:
        decoded_content = response.content.decode('utf-8')
        cr = csv.reader(decoded_content.splitlines(), delimiter=',')
        next(cr)  # Пропускаем заголовок
        for row in cr:
            class_map.append(row[2])
    return class_map

# Загружаем модель YAMNet и метки
yamnet_model_handle = 'https://tfhub.dev/google/yamnet/1'
yamnet_model = hub.load(yamnet_model_handle)
class_names = download_yamnet_class_map()


def load_wav_16k_mono(filename):
    wav, sr = sf.read(filename)
    if wav.ndim > 1:
        wav = np.mean(wav, axis=1)
    if sr != 16000:
        wav = librosa.resample(wav, orig_sr=sr, target_sr=16000)
    return wav


def predict_audio_label(audio_path):
    """
    Сегментация аудио
    На вход audio_path
    Возвращает класс звукового сегмента
    """
    wav_data = load_wav_16k_mono(audio_path)
    waveform = tf.convert_to_tensor(wav_data, dtype=tf.float32)
    scores, embeddings, spectrogram = yamnet_model(waveform)
    prediction = tf.reduce_mean(scores, axis=0)
    top_class = tf.argmax(prediction)
    return class_names[top_class]


def tags_from_audio(video_file):
    audio = extract_audio_to_wav(video_file)
    language = language_detect(audio)
    audio_label = predict_audio_label(audio)
    try:
        text = convert_audio_to_text(audio, language)
        adult = contains_profanity(text)
        text = translate_text(text)
        entags = generate_hashtags([text])[0]
        entags.append(audio_label)
        rutags = translate_text(entags, 'ru')
        return rutags, entags, adult
    except:
        return [translate_text(audio_label, 'ru')], [translate_text(audio_label)], False
