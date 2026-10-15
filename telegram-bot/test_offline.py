#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Офлайн-тест генератора и проверяльщика: python3 test_offline.py"""
import random
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ["TELEGRAM_TOKEN"] = "x"  # не нужен для теста
import spanish_bot as B

verbs = B.parse_yml(os.path.join(B.CURRICULUM, "verbs.yml"))
nouns = [n for n in B.parse_yml(os.path.join(B.CURRICULUM, "vocabulary.yml")) if "gender" in n]
print("verbs:", len(verbs), "| nouns:", len(nouns))
assert len(verbs) >= 30 and len(nouns) >= 15, "curriculum parse broken"
for v in verbs[:3]:
    assert len(v.get("forms", [])) == 6, v

random.seed(7)
kinds = {}
for i in range(300):
    ex = B.next_exercise(verbs, nouns)
    kinds[ex["type"]] = kinds.get(ex["type"], 0) + 1
    assert ex.get("prompt") and ex.get("show") or ex.get("correct"), ex
print("300 exercises:", kinds)

# эталонные ответы всегда принимаются
for i in range(150):
    ex = B.next_exercise(verbs, nouns)
    if ex["type"] == "mcq":
        ok, m = B.check(ex, ex["letter"])
    elif ex["type"] == "error":
        ok, m = B.check(ex, ex["show"])
    else:
        ok, m = B.check(ex, ex["refs"][0])
    assert ok == "ok", (ex, m)

# неправильный ответ ловится
ex = B.next_exercise(verbs, nouns)
while ex["type"] != "conjugation":
    ex = B.next_exercise(verbs, nouns)
ok, m = B.check(ex, "plimplim")
assert ok == "fail", m

# ударение: tú без accent -> снова просим
st = B.new_state()
ex = {"type": "translate", "word": "hablar",
      "prompt": "", "refs": [B.norm("tú hablas de español")], "show": "Tú hablas de español."}
ok, m = B.check(ex, "tu hablas de espanol")
print("accent-check verdict:", ok, "|", m[:60])
assert ok in ("again", "fail"), ok
ok2, _ = B.check(ex, "tú hablas de español")
assert ok2 == "ok"

# translate без местоимения — принимаем
ok3, _ = B.check(ex, "hablas de español")
assert ok3 == "ok", "no-pronoun variant must pass"

print("ALL TESTS PASSED ✔")
