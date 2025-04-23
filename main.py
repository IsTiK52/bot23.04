from dotenv import load_dotenv

import os
import json
import datetime
import telebot
from dotenv import load_dotenv
from telebot import types

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")

bot = telebot.TeleBot(BOT_TOKEN)

SCHEDULE_PATH = "words_schedule.json"
PROGRESS_PATH = "storage/progress.csv"
REPETITION_PATH = "storage/repetition.json"
ESSAY_DIR = "storage/essays"

with open(SCHEDULE_PATH, encoding="utf-8") as f:
    schedule = json.load(f)

def get_today_words():
    today = datetime.datetime.now().strftime("%Y-%m-%d")
    return schedule.get(today)

def check_word_usage(words, text):
    return [w["word"] for w in words if w["word"].lower() in text.lower()]

@bot.message_handler(commands=["start", "menu"])
def show_menu(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("📘 Слова дня", "✍️ Прислать эссе")
    markup.add("🔁 Повторение", "📊 Мой прогресс", "💰 Поддержать проект")
    bot.send_message(message.chat.id, "Привет! Я VocabularBot. Нажми кнопку:", reply_markup=markup)

@bot.message_handler(func=lambda m: m.text == "📘 Слова дня")
def words_today(message):
    data = get_today_words()
    if not data:
        bot.send_message(message.chat.id, "На сегодня слов нет.")
        return
    text = f"🎯 Тема: {data['theme']}\n\n"
    for w in data["words"]:
        text += f"🔹 *{w['word']}* ({w['pos']}) — {w['translation']}\n_{w['example']}_\n\n"
    bot.send_message(message.chat.id, text, parse_mode="Markdown")

@bot.message_handler(func=lambda m: m.text == "✍️ Прислать эссе")
def ask_essay(message):
    msg = bot.send_message(message.chat.id, "Пришли своё эссе одним сообщением.")
    bot.register_next_step_handler(msg, handle_essay)

def handle_essay(message):
    user_id = str(message.from_user.id)
    today = datetime.datetime.now().strftime("%Y-%m-%d")
    os.makedirs(ESSAY_DIR, exist_ok=True)
    path = f"{ESSAY_DIR}/{user_id}_{today}.txt"
    with open(path, "w", encoding="utf-8") as f:
        f.write(message.text)

    data = get_today_words()
    used = check_word_usage(data["words"], message.text)
    missed = [w["word"] for w in data["words"] if w["word"] not in used]

    try:
        with open(REPETITION_PATH, encoding="utf-8") as f:
            rep = json.load(f)
    except:
        rep = {}

    rep.setdefault(user_id, []).extend(missed)
    rep[user_id] = list(set(rep[user_id]))
    with open(REPETITION_PATH, "w", encoding="utf-8") as f:
        json.dump(rep, f, ensure_ascii=False, indent=2)

    with open(PROGRESS_PATH, "a", encoding="utf-8") as f:
        f.write(f"{user_id},{today},{len(data['words'])},{len(used)},yes\n")

    bot.send_message(message.chat.id, f"📝 Эссе получено.\n✅ Использовано слов: {len(used)} из {len(data['words'])}")
    bot.send_message(message.chat.id, "📊 GPT-анализ отключён. Спасибо!")

@bot.message_handler(func=lambda m: m.text == "🔁 Повторение")
def repeat_words(message):
    user_id = str(message.from_user.id)
    try:
        with open(REPETITION_PATH, encoding="utf-8") as f:
            rep = json.load(f)
        words = rep.get(user_id, [])
        if not words:
            raise ValueError
        text = "🔁 Повтори эти слова:\n" + "\n".join(f"🔁 {w}" for w in words)
        bot.send_message(message.chat.id, text)
    except:
        bot.send_message(message.chat.id, "Нет слов для повторения.")

@bot.message_handler(func=lambda m: m.text == "📊 Мой прогресс")
def show_progress(message):
    user_id = str(message.from_user.id)
    try:
        with open(PROGRESS_PATH, encoding="utf-8") as f:
            lines = f.readlines()[1:]
            count = len([l for l in lines if user_id in l])
            bot.send_message(message.chat.id, f"📈 Эссе сдано: {count}")
    except:
        bot.send_message(message.chat.id, "Нет данных.")

@bot.message_handler(func=lambda m: m.text == "💰 Поддержать проект")
def support(message):
    bot.send_message(message.chat.id, "Если хочешь поддержать проект ❤️\n📲 Kaspi Gold: +7 777 772 21 70\nСпасибо тебе огромное!")

bot.polling()
