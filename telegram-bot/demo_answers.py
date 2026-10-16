#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Демо: как выглядят ответы бота с переводом. python3 demo_answers.py"""
import os, random, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ["TELEGRAM_TOKEN"] = "x"
os.environ["ALLOWED_CHAT_IDS"] = "1"
import spanish_bot as B

verbs = B.parse_yml(os.path.join(B.CURRICULUM, "verbs.yml"))
nouns = [n for n in B.parse_yml(os.path.join(B.CURRICULUM, "vocabulary.yml")) if "gender" in n]
random.seed(3)


def strip_html(s):
    return re.sub(r"</?[bi]>", "", s).replace("<br>", "\n")


seen = {}
while len(seen) < 4:
    ex = B.next_exercise(verbs, nouns)
    if ex["type"] in seen:
        continue
    seen[ex["type"]] = ex

for kind, ex in seen.items():
    print("=" * 70)
    print("ЗАДАНИЕ:", strip_html(ex["prompt"]))
    if kind == "mcq":
        right, m_ok = B.check(ex, ex["letter"])
        wrong = "a" if ex["letter"] != "a" else "b"
        _, m_bad = B.check(ex, "какая-то чушь")
    elif kind == "error":
        right, m_ok = B.check(ex, ex["show"])
        _, m_bad = B.check(ex, ex["prompt"])
    else:
        right, m_ok = B.check(ex, ex["refs"][0])
        _, m_bad = B.check(ex, "plimplim")
    print("-- верный ответ ->")
    print(strip_html(m_ok))
    print("-- неверный ответ ->")
    print(strip_html(m_bad))
print("=" * 70)
