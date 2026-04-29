import pandas as pd
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
from PIL import Image, ImageDraw
import random

# --- Загружаем данные ---
data = pd.read_csv('countries.csv')
facts = pd.read_csv('facts.csv')


# --- Функции ---
def get_random_country():
    country = data.sample(1).iloc[0]
    return {
        'country': country['country'],
        'capital': country['capital'],
        'latitude': country['latitude'],
        'longitude': country['longitude']
    }
def get_funfact(country_name):
    filtered = facts[facts['country'].str.lower() == country_name.lower()]
    if filtered.empty:
        return None
    return random.choice(filtered['fact'].tolist())

def mark_capital_on_map(lat, lon, map_path='world_map.jpg'):
    map_img = Image.open(map_path)
    draw = ImageDraw.Draw(map_img)

    width, height = map_img.size
    x = int((lon + 180) * (width / 360))
    y = int((90 - lat) * (height / 180))

    size = 7  # длина линий крестика
    draw.line((x - size, y - size, x + size, y + size), fill='red', width=2)
    draw.line((x - size, y + size, x + size, y - size), fill='red', width=2)

    path = 'map_with_capital.jpg'
    map_img.save(path)
    return path


# --- Команды ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Привет! Я бот для изучения стран и столиц.\n"
        "Используй команду /quiz, чтобы начать викторину.\n"
        "Чтобы узнать все команды, отправьте /help."
    )
async def funfact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text(
            "Использование:\n/funfact Название_страны\n\nПример:\n/funfact Australia"
        )
        return

    country_name = " ".join(context.args)
    fact = get_funfact(country_name)

    if not fact:
        await update.message.reply_text(
            f"Фактов про страну «{country_name}» пока нет."
        )
        return

    await update.message.reply_text(
        f"Интересный факт о {country_name}:\n{fact}"
    )

async def quiz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    country_info = get_random_country()
    context.user_data['country_info'] = country_info
    map_path = mark_capital_on_map(country_info['latitude'], country_info['longitude'])

    with open(map_path, 'rb') as photo:
        await update.message.reply_photo(
            photo=photo,
            caption=f"Угадайте столицу этой страны: {country_info['country']}"
        )


async def answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if 'country_info' not in context.user_data:
        await update.message.reply_text("Сначала отправьте /quiz, чтобы начать викторину.")
        return

    user_answer = update.message.text.strip()
    correct_answer = context.user_data['country_info']['capital']

    if user_answer.lower() == correct_answer.lower():
        await update.message.reply_text("Верно!")
    else:
        await update.message.reply_text(f"Неверно! Правильный ответ: {correct_answer}")

    del context.user_data['country_info']


async def all_countries(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lines = [f"{row['country']} — {row['capital']}" for _, row in data.iterrows()]
    chunk_size = 30
    for i in range(0, len(lines), chunk_size):
        chunk = lines[i:i + chunk_size]
        text = "\n".join(chunk)
        await update.message.reply_text(text)


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Доступные команды:\n"
        "/start — приветствие и инструкция\n"
        "/quiz — начать викторину, угадать столицу\n"
        "/all — показать все страны с их столицами\n"
        "/hint — подсказка по текущей стране\n"
        "/funfact [страна] — показать интересный факт о стране\n"
        "/help — показать это сообщение"

    )


async def hint(update: Update, context: ContextTypes.DEFAULT_TYPE):
    country_info = context.user_data.get('country_info')
    if not country_info:
        await update.message.reply_text("Сначала используйте /quiz, чтобы выбрать страну.")
        return

    capital = country_info['capital']
    hint_text = capital[0] + "*" * (len(capital) - 1)
    await update.message.reply_text(f"Подсказка: {hint_text}")

# --- Запуск бота ---
if __name__ == "__main__":
    app = ApplicationBuilder().token("8282472753:AAHlw5Sfjnco0iKJHF2UtDdXD7ucqihd6GQ").build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("quiz", quiz))
    app.add_handler(CommandHandler("all", all_countries))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("hint", hint))
    app.add_handler(CommandHandler("funfact", funfact))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, answer))

    print("Бот запущен...")
    app.run_polling()
