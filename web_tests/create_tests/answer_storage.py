"""Lossless choice storage, with support for existing semicolon-separated data."""
import json
import re

PREFIX = '@answers:'


def split_answers(value):
    if value.startswith(PREFIX):
        answers = json.loads(value[len(PREFIX):])
        if not isinstance(answers, list) or not all(isinstance(a, str) for a in answers):
            raise ValueError('Invalid answer list')
        return answers
    # MathLive uses \; for spaces; these are not answer separators.
    return re.split(r'(?<!\\);', value) if value else []


def pack_answers(answers):
    return PREFIX + json.dumps(answers, ensure_ascii=False)


def display_answer(value, is_choice):
    if not is_choice:
        return value
    return '; '.join(value if isinstance(value, list) else split_answers(value))
