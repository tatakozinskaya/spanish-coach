#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Spanish Coach — Telegram-бот. Читает базу из ../curriculum/*.yml, даёт задания
с строгой проверкой (ударения/ñ обязательны). Только стандартная библиотека.

Команды: /start, /session, next, /stat, /help, /id
В 15:00 местного времени сам присылает старт сессии всем, кто писал /start.
"""
import json
import os
import random
import re
import time
import urllib.parse
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
CURRICULUM = os.path.join(HERE, os.pardir, "curriculum")
PROGRESS = os.path.join(HERE, os.pardir, "progress.md")
STATE_FILE = os.path.join(HERE, "state.json")
ENV_FILE = os.path.join(HERE, ".env")

SESSION_SIZE = 10
DAILY_HOUR, DAILY_MIN = 15, 0
POLL_TIMEOUT = 25

ACC = {"á": "a", "é": "e", "í": "i", "ó": "o", "ú": "u", "ñ": "n", "ü": "u"}
ACC_TABLE = str.maketrans(ACC)
PERSON_IDX = {"yo": 0, "tú": 1, "él": 2, "nosotros": 3, "ellos": 5}
SUBJ = {"yo": "Yo", "tú": "Tú", "él": "Él", "nosotros": "Nosotros", "ellos": "Ellos"}
SUBJ_RU = {"yo": "Я", "tú": "Ты", "él": "Он", "nosotros": "Мы", "ellos": "Они"}

TAILS_ES = {
    "hablar": "de español", "trabajar": "en una oficina", "estudiar": "español",
    "ayudar": "a mi madre", "tomar": "café por la mañana", "comer": "a las dos",
    "beber": "agua", "aprender": "palabras nuevas", "vivir": "en Novosibirsk",
    "escribir": "un correo", "correr": "por la mañana", "necesitar": "agua",
    "recibir": "un mensaje", "caminar": "en el parque", "ser": "de Rusia",
    "estar": "en casa", "ir": "al trabajo", "tener": "dos gatos",
    "hacer": "los deberes", "poder": "ayudarme", "querer": "aprender español",
    "decir": "la verdad", "venir": "a las cinco", "saber": "la respuesta",
    "dormir": "mucho", "jugar": "en el parque", "ver": "una película",
    "dar": "un café", "poner": "el libro en la mesa", "salir": "a las nueve",
    "abrir": "la puerta", "vender": "un coche",
}
TAILS_RU = {
    "de español": "по-испански", "en una oficina": "в офисе", "español": "испанский",
    "a mi madre": "маме", "café por la mañana": "кофе утром", "a las dos": "в два часа",
    "agua": "воду", "palabras nuevas": "новые слова", "en Novosibirsk": "в Новосибирске",
    "un correo": "письмо", "por la mañana": "утром", "de Rusia": "из России",
    "en casa": "дома", "al trabajo": "на работу", "dos gatos": "двух кошек",
    "los deberes": "уроки", "ayudarme": "мне помочь", "aprender español": "учить испанский",
    "la verdad": "правду", "a las cinco": "в пять", "mucho": "много",
    "una película": "фильм", "la respuesta": "ответ", "un mensaje": "сообщение",
    "en el parque": "в парке", "un café": "кофе", "a las nueve": "в девять",
    "el libro en la mesa": "книгу на стол", "la puerta": "дверь", "un coche": "машину",
}

# ---------- русские переводы фраз (для разбора ответа) ----------
# Формы по лицам в том же порядке, что PERSON_IDX: yo, tú, él, nosotros, ellos.
RU_FORMS = {
    "hablar": "говорю, говоришь, говорит, говорим, говорят",
    "trabajar": "работаю, работаешь, работает, работаем, работают",
    "estudiar": "изучаю, изучаешь, изучает, изучаем, изучают",
    "ayudar": "помогаю, помогаешь, помогает, помогаем, помогают",
    "tomar": "пью, пьёшь, пьёт, пьём, пьют",
    "beber": "пью, пьёшь, пьёт, пьём, пьют",
    "comer": "ем, ешь, ест, едим, едят",
    "aprender": "учу, учишь, учит, учим, учите",
    "vivir": "живу, живёшь, живёт, живём, живут",
    "escribir": "пишу, пишешь, пишет, пишем, пишут",
    "correr": "бегаю, бегаешь, бегает, бегаем, бегают",
    "necesitar": "нуждаюсь, нуждаешься, нуждается, нуждаемся, нуждаются",
    "recibir": "получаю, получаешь, получает, получаем, получают",
    "caminar": "гуляю, гуляешь, гуляет, гуляем, гуляют",
    "ir": "иду, идёшь, идёт, идём, идут",
    "hacer": "делаю, делаешь, делает, делаем, делают",
    "poder": "могу, можешь, может, можем, могут",
    "querer": "хочу, хочешь, хочет, хотим, хотят",
    "decir": "говорю, говоришь, говорит, говорим, говорят",
    "venir": "прихожу, приходишь, приходит, приходим, приходят",
    "saber": "знаю, знаешь, знает, знаем, знают",
    "poner": "кладу, кладёшь, кладёт, кладём, кладут",
    "salir": "выхожу, выходишь, выходит, выходим, выходят",
    "dormir": "сплю, спишь, спит, спим, спят",
    "jugar": "играю, играешь, играет, играем, играют",
    "ver": "смотрю, смотришь, смотрит, смотрим, смотрят",
    "dar": "даю, даёшь, даёт, даём, дают",
    "abrir": "открываю, открываешь, открывает, открываем, открывают",
    "vender": "продаю, продаёшь, продаёт, продаём, продают",
    "levantarse": "встаю, встаёшь, встаёт, встаём, встают",
    "acostarse": "ложусь спать, ложишься спать, ложится спать, ложимся спать, ложатся спать",
}
# ПереводRussian-дополнения, если буквальный вариант не по-русски.
RU_TAIL_FIX = {("necesitar", "agua"): "в воде", ("poder", "ayudarme"): "помочь",
               ("tener", "dos gatos"): "две кошки"}
# Личное местоимение по-русски не нужно (иначе «Я меня зовут»).
RU_NO_SUBJ = {"llamarse": "меня зовут, тебя зовут, его зовут, нас зовут, их зовут"}
RU_TENER = "у меня, у тебя, у него, у нас, у них"
# Индекс в 5-элементных списках переводов (vosotros не переводим)
RU_IDX = {"yo": 0, "tú": 1, "él": 2, "nosotros": 3, "ellos": 4}


def ru_phrase(inf, person, tail_es=None):
    """Естественный перевод фразы «SUBJ form tail»: «Она идёт на работу»."""
    i = RU_IDX.get(person, 0)
    tail_ru = ""
    if tail_es:
        tail_ru = RU_TAIL_FIX.get((inf, tail_es), TAILS_RU.get(tail_es, ""))
    subj = SUBJ_RU[person]
    if inf == "ser":
        txt = "%s — %s" % (subj, tail_ru) if tail_ru else "%s есть (кто-то)" % subj
    elif inf == "estar":
        txt = "%s %s" % (subj, tail_ru) if tail_ru else "%s находится (где-то)" % subj
    elif inf == "tener":
        who = RU_TENER.split(", ")[i]
        txt = "%s есть %s" % (who, tail_ru) if tail_ru else "%s есть (что-то)" % who
    elif inf in RU_NO_SUBJ:
        txt = RU_NO_SUBJ[inf].split(", ")[i]
    else:
        forms = RU_FORMS.get(inf)
        if not forms:
            return ""
        txt = "%s %s %s" % (subj, forms.split(", ")[i], tail_ru)
    return re.sub(r"\s+", " ", txt).strip()


def cap_ru(s):
    return (s[:1].upper() + s[1:]) if s else s


def ru_line(ex):
    """Строка перевода фразы, с которой шла работа ('' если перевода нет)."""
    ru = (ex.get("ru") or "").strip()
    return "🇷🇺 <i>%s</i>" % ru if ru else ""

# ---------- config / state ----------

def load_token():
    tok = os.environ.get("TELEGRAM_TOKEN")
    if tok:
        return tok.strip()
    if os.path.exists(ENV_FILE):
        for line in open(ENV_FILE, encoding="utf-8"):
            if line.strip().startswith("TELEGRAM_TOKEN="):
                return line.split("=", 1)[1].strip()
    raise SystemExit("Нет токена: %s (строка TELEGRAM_TOKEN=...)" % ENV_FILE)

def load_allowed_ids():
    """Белый список chat_id через запятую: ALLOWED_CHAT_IDS=123,456 в .env или окружении."""
    raw = os.environ.get("ALLOWED_CHAT_IDS", "")
    if not raw and os.path.exists(ENV_FILE):
        for line in open(ENV_FILE, encoding="utf-8"):
            if line.strip().startswith("ALLOWED_CHAT_IDS="):
                raw = line.split("=", 1)[1]
    ids = {int(x) for x in re.findall(r"-?\d+", raw)}
    if not ids:
        raise SystemExit("Не задан ALLOWED_CHAT_IDS — бот не знает, кому отвечать (см. .env)")
    return ids

def load_states():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_states(states):
    tmp = STATE_FILE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(states, f, ensure_ascii=False, indent=1)
    os.replace(tmp, STATE_FILE)

def new_state():
    return {"exercise": None, "left": 0, "correct": 0, "asked": 0,
            "wrong": [], "repeat": [], "retries": 0, "last_daily": ""}

# ---------- curriculum ----------

def parse_yml(path):
    text = open(path, encoding="utf-8").read()
    # склейка переносов внутри записей: только если следующая строка
    # начинается не с '-', не с '#' и это не пустая строка
    text = re.sub(r"\n[ \t]+(?=[^\s\-#])", " ", text)
    out = []
    for block in re.findall(r"- \{(.+?)\}(?:\n|$)", text):
        e = {}
        for m in re.finditer(r'(\w+):\s*(\[[^\]]*\]|"(?:[^"\\]|\\.)*"|[^,{}]+)', block):
            k, v = m.group(1), m.group(2).strip()
            if v.startswith("["):
                e[k] = [x.strip() for x in v[1:-1].split(",") if x.strip()]
            elif v.startswith('"'):
                e[k] = v[1:-1]
            else:
                e[k] = int(v) if re.fullmatch(r"\d+", v) else v
        if e:
            out.append(e)
    return out

# ---------- Telegram API ----------

TOKEN = load_token()
ALLOWED_IDS = load_allowed_ids()

def tg(method, **kw):
    url = "https://api.telegram.org/bot%s/%s" % (TOKEN, method)
    try:
        data = urllib.parse.urlencode(kw).encode()
        with urllib.request.urlopen(urllib.request.Request(url, data=data),
                                    timeout=POLL_TIMEOUT + 10) as r:
            return json.load(r)
    except Exception as ex:
        print("tg %s error: %s" % (method, ex), flush=True)
        return {"ok": False}

def send(chat_id, text):
    tg("sendMessage", chat_id=chat_id, text=text, parse_mode="HTML",
       disable_web_page_preview="true")

# ---------- генерация заданий ----------

def ru_of(v):
    return v.get("ru", v["inf"]).split("(")[0].split(";")[0].split(",")[0].strip()

def gen_translate(verbs):
    pool = [v for v in verbs if v.get("level") == 1
            and v["type"] != "pronominal" and v["inf"] in TAILS_ES] or verbs
    v = random.choice(pool)
    person = random.choice(list(PERSON_IDX))
    form = v["forms"][PERSON_IDX[person]]
    tail = TAILS_ES[v["inf"]]
    ru = cap_ru(ru_phrase(v["inf"], person, tail))
    full = "%s %s %s" % (SUBJ[person], form, tail)
    no_pron = "%s %s" % (form, tail)
    return {"type": "translate", "word": v["inf"], "prompt": "✍️ Переведи на испанский:\n«%s»" % ru,
            "refs": [norm(full), norm(no_pron)], "show": "%s." % full,
            "ru": ru}

def gen_conjugation(verbs):
    pool = [v for v in verbs if v.get("level") == 1] or verbs
    irr = [v for v in pool if v["type"] in ("irregular", "pronominal")]
    if irr and random.random() < 0.5:
        pool = irr
    v = random.choice(pool)
    person = random.choice(list(PERSON_IDX))
    form = v["forms"][PERSON_IDX[person]]
    return {"type": "conjugation", "word": v["inf"],
            "prompt": "🔤 Раскрой скобки: %s ____ (%s)" % (SUBJ[person], v["inf"]),
            "refs": [norm(form)], "show": "%s %s." % (SUBJ[person], form),
            "ru": cap_ru(ru_phrase(v["inf"], person))}

def gen_mcq(verbs, nouns):
    if random.random() < 0.6:
        v = random.choice([x for x in verbs if x.get("level") == 1] or verbs)
        person = random.choice(list(PERSON_IDX))
        correct = v["forms"][PERSON_IDX[person]]
        wrongs = {f for f in v["forms"] if f != correct}
        if correct.endswith("o"):
            wrongs.add(correct[:-1] + "a")  # вымышленная, но правдоподобная (*haco-тип)
        opts = [correct] + random.sample(sorted(wrongs), min(3, len(wrongs)))
        random.shuffle(opts)
        letters = "abcd"
        line = "   ".join("%s) %s" % (letters[i], o) for i, o in enumerate(opts))
        tail = TAILS_ES.get(v["inf"], "…")
        return {"type": "mcq", "word": v["inf"],
                "prompt": "☝️ Выбери вариант: %s ____ %s\n%s" % (SUBJ[person], tail, line),
                "letter": letters[opts.index(correct)], "correct": correct,
                "opts": {letters[i]: o for i, o in enumerate(opts)},
                "ru": cap_ru(ru_phrase(v["inf"], person, tail))}
    pool = [n for n in nouns if n.get("level") == 1] or nouns
    n = random.choice(pool)
    correct_art = "el" if n["gender"] in ("m", "f1") else "la"
    wrong_art = "la" if correct_art == "el" else "el"
    noun = re.sub(r"^(el|la) ", "", n["es"]).split(" /")[0]
    opts = ["%s %s" % (a, noun) for a in (correct_art, wrong_art)]
    random.shuffle(opts)
    return {"type": "mcq", "word": n["es"],
            "prompt": "☝️ Выбери вариант: ____ %s\na) %s   b) %s" % (noun, opts[0], opts[1]),
            "letter": "ab"[opts.index("%s %s" % (correct_art, noun))],
            "correct": "%s %s" % (correct_art, noun),
            "opts": {"a": opts[0], "b": opts[1]},
            "ru": "это «%s»" % n.get("ru", "")}

BROKEN = {"hago": "haco", "tengo": "teno", "voy": "vovo", "soy": "so",
          "duermo": "dormo", "juego": "jugo", "salgo": "salo", "pongo": "pono",
          "hacemos": "hacemos ", "ayudo": "aydo", "hablamos": "hablmos"}

def gen_error(verbs):
    pool = [v for v in verbs if v.get("level") == 1 and v["inf"] in TAILS_ES] or verbs
    for _ in range(20):
        v = random.choice(pool)
        person = random.choice(["yo", "tú", "él"])
        correct = v["forms"][PERSON_IDX[person]]
        broken = BROKEN.get(correct)
        if not broken:
            other = random.choice([p for p in ("yo", "tú", "él", "nosotros", "ellos")
                                   if p != person])
            broken = v["forms"][PERSON_IDX[other]]
            if broken == correct:
                continue
        sent = "%s %s %s." % (SUBJ[person], correct, TAILS_ES[v["inf"]])
        bad = sent.replace(correct, broken, 1)
        if bad == sent:
            continue
        hint = v.get("note", "")
        return {"type": "error", "word": v["inf"],
                "prompt": "🔎 Найди ошибку: «%s»" % bad,
                "refs": [norm(sent)], "show": sent, "broken": broken,
                "correct": correct, "note": hint,
                "ru": cap_ru(ru_phrase(v["inf"], person, TAILS_ES[v["inf"]]))}
    return gen_conjugation(verbs)

def next_exercise(verbs, nouns):
    r = random.random()
    if r < 0.30:
        return gen_translate(verbs)
    if r < 0.55:
        return gen_conjugation(verbs)
    if r < 0.80:
        return gen_mcq(verbs, nouns)
    return gen_error(verbs)

# ---------- проверка (strict) ----------

def norm(s):
    s = s.strip().lower()
    s = re.sub(r"[.!¡¿?]+$", "", s)
    s = re.sub(r"^(yo|tú|tu|él|el|nosotros|ella|ellos)\s+", "", s)  # субъект не важен
    return re.sub(r"\s+", " ", s).strip()

def strip_acc(s):
    return s.translate(ACC_TABLE)

def check(ex, answer):
    """-> (verdict, message). verdict: 'ok' | 'again' | 'fail'.
    Strict: эталон сверяется с ударениями; 'похоже, но без ударений/ñ' -> again."""
    a = norm(answer)
    raw = re.sub(r"[.!¡¿?]+$", "", answer.strip().lower())
    raw = re.sub(r"\s+", " ", raw)

    def accent_lacking(ref):
        # то же слово, но потеряны ударные знаки
        return strip_acc(raw) == strip_acc(ref.lower()) and raw != ref.lower()

    if ex["type"] == "mcq":
        word = a.rstrip(").")
        if len(word) <= 2 and word in "abcd ":
            good = word.strip() == ex["letter"]
        else:
            good = word == norm(ex["correct"])
        extra = ("\n" + ru_line(ex)) if ru_line(ex) else ""
        if good:
            return "ok", "✅ Правильно! <b>%s</b>%s" % (ex["correct"], extra)
        return "fail", ("❌ Правильный ответ: <b>%s) %s</b>%s"
                        % (ex["letter"], ex["correct"], extra))

    if ex["type"] == "error":
        extra = ("\n" + ru_line(ex)) if ru_line(ex) else ""
        targets = ex["refs"] + [norm(ex["show"])]
        if a in targets:
            # совпало по буквам — но все ли ударения на месте?
            if accent_lacking(ex["show"]):
                return "again", ("⚠️ Почти! Пропущено ударение/ñ — в испанском это "
                                 "другие слова (tú ≠ tu, año ≠ ano).\nНапиши ещё раз 👇")
            return "ok", "✅ Верно! <b>%s</b>%s" % (ex["show"], extra)
        fixed = answer
        if ex.get("broken") and ex["broken"].strip() in answer:
            fixed = answer.replace(ex["broken"].strip(), ex["correct"])
        if norm(fixed) in targets:
            return "ok", "✅ Верно! <b>%s</b>%s" % (ex["show"], extra)
        return "fail", ("❌ Ошибка была: <i>%s → %s</i>\nПравильно: <b>%s</b>%s%s"
                        % (ex["broken"], ex["correct"], ex["show"], extra,
                           ("\n💡 " + ex["note"]) if ex.get("note") else ""))

    # translate / conjugation
    #subject-ловушка: «tu hablas» при ожидаемом «tú hablas» (norm съедает местоимение)
    SUBJ_FIX = {"tu": "tú", "el": "él"}
    first = raw.split(" ", 1)[0] if raw else ""
    show_l = ex["show"].lower()
    if first in SUBJ_FIX and show_l.startswith(SUBJ_FIX[first] + " "):
        return "again", ("⚠️ Внимание: <b>%s</b> пишется с ударением — без него это «%s». "
                         "Напиши ещё раз 👇"
                         % (SUBJ_FIX[first], {"tu": "твой", "el": "артикль"}[first]))
    if a in ex["refs"]:
        for ref in ex["refs"]:
            if strip_acc(a) == strip_acc(ref) and a != ref:
                return "again", ("⚠️ Почти! Пропущено ударение или ñ — а это разные "
                                 "слова: <b>tú</b> «ты» ≠ <i>tu</i> «твой», "
                                 "<b>año</b> «год» ≠ <i>ano</i>.\nНапиши ещё раз "
                                 "правильно 👇")
        extra = ("\n" + ru_line(ex)) if ru_line(ex) else ""
        return "ok", "✅ Отлично! <b>%s</b>%s" % (ex["show"], extra)
    if any(strip_acc(a) == strip_acc(r) for r in ex["refs"]):
        return "again", ("⚠️ Почти! Буквы те, но потеряны ударения/ñ. В испанском "
                         "это меняет смысл: <b>tú</b> «ты» ≠ <i>tu</i> «твой», "
                         "<b>sí</b> «да» ≠ <i>si</i> «если».\nНапиши ещё раз 👇")
    extra = ("\n" + ru_line(ex)) if ru_line(ex) else ""
    return "fail", "❌ Правильно: <b>%s</b>%s" % (ex["show"], extra)

# ---------- сессия ----------

REPO = os.path.abspath(os.path.join(HERE, os.pardir))

def git_push_session():
    """Закоммитить прогресс и запушить в GitHub (SSH). Ошибки — только в лог."""
    import subprocess
    env = dict(os.environ, GIT_SSH_COMMAND="ssh -o BatchMode=yes",
               GIT_AUTHOR_NAME="Tata Kozinska", GIT_AUTHOR_EMAIL="t.kozinskaya@2gis.ru",
               GIT_COMMITTER_NAME="Tata Kozinska", GIT_COMMITTER_EMAIL="t.kozinskaya@2gis.ru")
    try:
        subprocess.run(["git", "add", "progress.md"], cwd=REPO, env=env,
                       capture_output=True, timeout=30, check=True)
        r = subprocess.run(["git", "commit", "-m",
                            "progress: сессия %s" % time.strftime("%Y-%m-%d %H:%M")],
                           cwd=REPO, env=env, capture_output=True, timeout=30)
        if r.returncode != 0:
            return  # нечего коммитить
        p = subprocess.run(["git", "push", "-q"], cwd=REPO, env=env,
                           capture_output=True, timeout=60)
        if p.returncode != 0:
            print("git push failed:", p.stderr.decode()[:200], flush=True)
    except Exception as ex:
        print("git_push_session:", ex, flush=True)

def give_ex(state, verbs, nouns):
    if state["repeat"] and random.random() < 0.6:
        word = state["repeat"].pop(0)
        v = next((x for x in verbs if x["inf"] == word), None)
        if v:
            ex = gen_conjugation([v])
            ex["prompt"] = "🔁 Повтор: " + ex["prompt"].split(": ", 1)[-1]
            state["exercise"] = ex
            return ex
    state["exercise"] = next_exercise(verbs, nouns)
    return state["exercise"]

def start_session(state, verbs, nouns):
    state.update(left=SESSION_SIZE, correct=0, asked=0, wrong=[], retries=0)
    state["last_daily"] = time.strftime("%Y-%m-%d")
    ex = give_ex(state, verbs, nouns)
    return ("🎯 <b>¡Vamos!</b> Тренировка: %d заданий. Проверка строгая — "
            "пиши с ударениями 😉\n\n%s" % (SESSION_SIZE, ex["prompt"]))

def finish_session(state):
    try:
        with open(PROGRESS, "a", encoding="utf-8") as f:
            f.write("\n## %s (Telegram) — %d/%d\n- Weak: %s\n" % (
                time.strftime("%Y-%m-%d %H:%M"), state["correct"], SESSION_SIZE,
                ", ".join(sorted(set(state["wrong"]))) or "нет"))
    except Exception as ex:
        print("progress:", ex, flush=True)
    git_push_session()
    weak = ", ".join(sorted(set(state["wrong"]))) or "нет 🎉"
    return ("🏁 Итог: <b>%d/%d</b> (%d%%).\nЗона внимания: <b>%s</b> — выпадет чаще "
            "в следующий раз.\n¡Muy bien, Tatiana! 💪"
            % (state["correct"], SESSION_SIZE,
               round(100 * state["correct"] / SESSION_SIZE), weak))

WELCOME = ("👋 <b>¡Hola! Я Spanish Coach.</b>\n\n"
           "/session — тренировка на %d заданий\nnext — пропустить\n"
           "/stat — счёт\n/help — как набирать ñ и ударения\n\n"
           "Каждый день в %02d:%02d сам предложу тренировку. ¡Hasta luego! 🇪🇸"
           % (SESSION_SIZE, DAILY_HOUR, DAILY_MIN))

HELP = ("⌨️ <b>Испанские буквы на macOS</b>\n\n"
        "Раскладка <b>Spanish (Latin American)</b> (System Settings → Keyboard → +):\n"
        "• ñ — клавиша справа от L\n• á é í ó ú — ´ затем гласная\n• ¡ ¿ — справа от Shift\n\n"
        "Обычная ABC: ñ=⌥N • á=⌥E+a • ¡=⌥1 • ¿=⌥⇧?\n"
        "Или удерживай клавишу 1-2 сек и выбери цифру.")

def handle(cid, text, state, verbs, nouns):
    low = text.strip().lower().rstrip("!?.")
    if low.startswith("/start"):
        send(cid, WELCOME)
    elif low.startswith("/help"):
        send(cid, HELP)
    elif low.startswith("/id"):
        send(cid, "chat_id: <code>%s</code>" % cid)
    elif low.startswith("/stat"):
        send(cid, "Сессия: %d/%d задано, верно %d. Осталось %d."
             % (state["asked"], SESSION_SIZE, state["correct"], state["left"])
             if state["left"] else "Сессия не идёт. /session — начать!")
    elif low.startswith("/session") or low in ("давай", "начали", "поехали"):
        send(cid, start_session(state, verbs, nouns))
    elif low in ("next", "дальше", "пропусти", "skip") and state["left"]:
        state["left"] -= 1
        w = state["exercise"].get("word")
        if w:
            state["wrong"].append(w)
            state["repeat"].append(w)
        ex = give_ex(state, verbs, nouns)
        send(cid, "Пропускаю (слово в зону внимания 🙂)\n\n%s" % ex["prompt"])
    elif state["left"] <= 0 or not state["exercise"]:
        send(cid, "Сессия не идёт. Напиши /session! 💪")
    else:
        ex = state["exercise"]
        verdict, msg = check(ex, text)
        if verdict == "again":
            send(cid, msg)  # без списания попытки, но повтор слова всё равно будет
            w = ex.get("word")
            if w and w not in state["wrong"]:
                state["wrong"].append(w)
            return
        state["asked"] += 1
        state["left"] -= 1
        if verdict == "ok":
            state["correct"] += 1
            if state["left"] <= 0:
                send(cid, msg + "\n\n" + finish_session(state))
                state["exercise"] = None
                return
            ex = give_ex(state, verbs, nouns)
            send(cid, "%s\n\nОсталось %d.\n\n%s" % (msg, state["left"], ex["prompt"]))
        else:
            w = ex.get("word")
            if w:
                if w not in state["wrong"]:
                    state["wrong"].append(w)
                state["repeat"].extend([w, w])
            if state["left"] <= 0:
                send(cid, msg + "\n\n" + finish_session(state))
                state["exercise"] = None
                return
            ex = give_ex(state, verbs, nouns)
            send(cid, "%s\n(вернётся 🔁) Идём дальше:\n\n%s" % (msg, ex["prompt"]))

# ---------- главный цикл ----------

def main():
    verbs = parse_yml(os.path.join(CURRICULUM, "verbs.yml"))
    nouns = parse_yml(os.path.join(CURRICULUM, "vocabulary.yml"))
    nouns = [n for n in nouns if "gender" in n]
    adjs = [n for n in nouns if "gender" not in n]
    print("Bot up: %d verbs, %d nouns" % (len(verbs), len(nouns)), flush=True)
    offset = 0
    offset_file = STATE_FILE + ".offset"
    if os.path.exists(offset_file):
        offset = int(open(offset_file).read().strip() or 0)
    while True:
        r = tg("getUpdates", offset=offset + 1, timeout=POLL_TIMEOUT,
               allowed_updates='["message"]')
        now = time.localtime()
        daily_key = time.strftime("%Y-%m-%d")
        states = load_states()
        dirty = False
        if r.get("ok"):
            for upd in r["result"]:
                offset = max(offset, upd["update_id"])
                msg = upd.get("message") or {}
                cid = (msg.get("chat") or {}).get("id")
                text = msg.get("text")
                if not cid or not text or msg.get("from", {}).get("is_bot"):
                    continue
                if cid not in ALLOWED_IDS:
                    # чужие сообщения игнорируем молча; bcc-заглушка — чтобы не светить whitelist
                    print("ignored from chat_id %s" % cid, flush=True)
                    continue
                st = states.setdefault(str(cid), new_state())
                handle(cid, text, st, verbs, nouns)
                states[str(cid)] = st
                dirty = True
        if (now.tm_hour, now.tm_min) >= (DAILY_HOUR, DAILY_MIN):
            for k, st in states.items():
                if int(k) not in ALLOWED_IDS:
                    continue
                if st.get("last_daily") != daily_key and st.get("left", 0) <= 0:
                    st["last_daily"] = daily_key
                    send(int(k), "🕒 <b>¡Buenas tardes!</b> 15:00 — время тренировки.\n\n"
                        + start_session(st, verbs, nouns))
                    dirty = True
        if dirty:
            save_states(states)
        with open(offset_file, "w") as f:
            f.write(str(offset))

if __name__ == "__main__":
    main()
