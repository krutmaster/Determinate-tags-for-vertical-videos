from predproc import extract_frames
from tagsuserdescr import tags_from_user_descr
from tagsvideo import tags_from_video
# from tagstextvideo import tags_from_text
from tagsaudio import tags_from_audio
from db import add_video_with_tags
import time
import os
import csv
from contextlib import suppress


def detect_porn_action(tags):
    """Only english tags!!!"""
    forbidden = [
        "fuck",
        "shit",
        "bitch",
        "sss",
        "dick",
        "pussy",
        "cock",
        "cum",
        "tits",
        "asshole",
        "motherfucker",
        "bastard",
        "damn",
        "slut",
        "whore",
        "prick",
        "cunt",
        "goddamn",
        "balls",
        "jerk-off",
        'orgy'
    ]
    for bad_word in forbidden:
        if bad_word in tags:
            return True
    return False


def main(video_file, user_descr, video_link):
    start = time.time()
    frames, frames_for_text, duration = extract_frames(video_file)
    rutags_1, entags_1, adult_1 = tags_from_user_descr(user_descr)
    rutags_2, entags_2 = tags_from_video(frames)
    if detect_porn_action(entags_2):
        print('Порнуха!')
        return False
    # rutags_3, entags_3, adult_2 = tags_from_text(frames_for_text) Не успели отладить
    rutags_3, entags_3, adult_2 = tags_from_audio(video_file)
    rutags = set(rutags_1) | set(rutags_2) | set(rutags_3)
    entags = set(entags_1) | set(entags_2) | set(entags_3)
    adult = adult_1 or adult_2
    dbname = 'postgres'
    user = 'uploader'
    password = '456'
    host = 'localhost'
    port = '5432'
    add_video_with_tags(dbname, user, password, host, port, video_link, duration, user_descr, adult, rutags, entags)
    print(time.time() - start)


def csv_to_dict(file_path):
    with open(file_path, mode='r', encoding='utf-8') as csv_file:
        csv_reader = csv.DictReader(csv_file)
        data = [row for row in csv_reader]
    return data


if __name__ == '__main__':
    dataset = csv_to_dict('yappy_hackaton_2024_400k.csv')
    listdir = os.listdir('D:\yappy_dataset')
    for i in range(len(listdir)):
        if i > 0:
            with suppress(Exception):
                video_file = f'D:\yappy_dataset\\{i}_fhd.mp4'
                print(i, video_file)
                user_descr = dataset[i]['description']
                link = dataset[i]['link']
                main(video_file, user_descr, link)
