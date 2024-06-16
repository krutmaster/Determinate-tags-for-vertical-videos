from common import generate_hashtags, contains_profanity, translate_text


def tags_from_user_descr(user_descr):
    entags = generate_hashtags([translate_text(user_descr)])[0]
    adult = contains_profanity(user_descr)
    rutags = translate_text(entags, 'ru')
    return rutags, entags, adult
