import telebot
import json
import datetime
import os
from telebot import types

BOT_TOKEN = os.environ.get("BOT_TOKEN")
bot = telebot.TeleBot(BOT_TOKEN)

# Пути
SCHEDULE_PATH = "words_schedule.json"
PROGRESS_PATH = "storage/progress.csv"
REPETITION_PATH = "storage/repetition.json"

# Словарь на сегодня
def get_today_words():
    today = datetime.datetime.now().strftime("%Y-%m-%d")
    with open(SCHEDULE_PATH, encoding="utf-8") as f:
        schedule = json.load(f)
    return schedule.get(today)

# Команды
@bot.message_handler(commands=["start", "menu"])
def menu(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("📘 Слова дня", "🔁 Повторение", "📊 Мой прогресс", "💰 Поддержать проект")
    bot.send_message(message.chat.id, "Привет! Я VocabularBot. Выбери действие:", reply_markup=markup)

# Обработка кнопок
@bot.message_handler(func=lambda m: True)
def handle(message):
    if message.text == "📘 Слова дня":
        data = get_today_words()
        if not data:
            bot.send_message(message.chat.id, "На сегодня слов нет.")
            return
        theme = data["theme"]
        words = data["words"]
        text = f"🎯 Тема: {theme}\n\n"
        for w in words:
            text += f"🔹 *{w['word']}* ({w['pos']}) — {w['translation']}\n_{w['example']}_\n\n"
        bot.send_message(message.chat.id, text, parse_mode="Markdown")

        # Запись в прогресс
        user_id = str(message.from_user.id)
        today = datetime.datetime.now().strftime("%Y-%m-%d")
        with open(PROGRESS_PATH, "a", encoding="utf-8") as f:
            f.write(f"{user_id},{today}\n")

        # Добавляем в повторение
        with open(REPETITION_PATH, encoding="utf-8") as f:
            rep = json.load(f)
        rep.setdefault(user_id, []).extend([w["word"] for w in words])
        rep[user_id] = list(set(rep[user_id]))
        with open(REPETITION_PATH, "w", encoding="utf-8") as f:
            json.dump(rep, f, ensure_ascii=False, indent=2)

    elif message.text == "🔁 Повторение":
        user_id = str(message.from_user.id)
        with open(REPETITION_PATH, encoding="utf-8") as f:
            rep = json.load(f)
        words = rep.get(user_id, [])
        if not words:
            bot.send_message(message.chat.id, "Нет слов для повторения.")
        else:
            text = "🔁 Повторение:\n\n" + "\n".join(f"🔹 {w}" for w in words)
            bot.send_message(message.chat.id, text)

    elif message.text == "📊 Мой прогресс":
        user_id = str(message.from_user.id)
        try:
            with open(PROGRESS_PATH, encoding="utf-8") as f:
                lines = f.readlines()
            count = sum(1 for line in lines if user_id in line)
            bot.send_message(message.chat.id, f"📈 Пройдено дней: {count}")
        except FileNotFoundError:
            bot.send_message(message.chat.id, "Прогресс пока пуст.")

    elif message.text == "💰 Поддержать проект":
        bot.send_message(message.chat.id, "Если хочешь поддержать проект ❤️\n📲 Kaspi Gold: +7 777 772 21 70")

bot.polling()
