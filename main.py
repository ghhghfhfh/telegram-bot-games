import os
import logging
from hearts import setup_handlers
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackContext,
    CallbackQueryHandler,
    MessageHandler,
    filters
)
from my_tetris import Tetris
from flask import Flask, send_from_directory
import threading

# ===== ИНИЦИАЛИЗАЦИЯ =====
load_dotenv()  # Загружаем переменные из .env

# ===== НАСТРОЙКА ЛОГИРОВАНИЯ =====
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ===== КОНФИГУРАЦИЯ =====
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
if not TOKEN:
    logger.error("Токен не найден! Проверьте .env файл")
    exit(1)

# Глобальное хранилище игр в тетрис
games = {}

# ===== FLASK SERVER ДЛЯ HTML-ФАЙЛОВ =====
app = Flask(__name__)

@app.route('/')
def index():
    return "Сервер запущен для обслуживания HTML-файлов"

@app.route('/<path:filename>')
def serve_file(filename):
    try:
        return send_from_directory('.', filename)
    except FileNotFoundError:
        return "Файл не найден", 404

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    logger.info(f"Запуск Flask на порту: {port}")
    app.run(host='0.0.0.0', port=port)

# Запускаем Flask в отдельном потоке
threading.Thread(target=run_flask, daemon=True).start()

# ===== ГАРАНТИРОВАННО РАБОЧИЕ ССЫЛКИ НА ИГРЫ =====
HEART_GAME_URL = "https://rawcdn.githack.com/ghhghfhfh/telegram-bot-games/refs/heads/main/hearts.html"
TETRIS_GAME_URL = "https://rawcdn.githack.com/ghhghfhfh/telegram-bot-games/refs/heads/main/tetris.html"

# ===== ОБРАБОТЧИКИ КОМАНД =====
async def start(update: Update, context: CallbackContext) -> None:
    await update.message.reply_text(
        "Привет! Я многофункциональный бот.\n"
        "Используй команды:\n"
        "/start - показать это сообщение\n"
        "/help - показать справку\n"
        "/tetris - начать игру в тетрис\n"
        "/stop - завершить игру\n"
        "/heartgame - открыть игру с сердечками\n"
        "/webtetris - открыть веб-версию тетриса\n"
        "/love - получить красивое сердечко"
    )

async def help_command(update: Update, context: CallbackContext) -> None:
    await update.message.reply_text(
        "🎮 Доступные функции:\n\n"
        "1. Команда любви:\n"
        "   /love - получить красивое сердечко\n\n"
        "2. Игра в тетрис:\n"
        "   /tetris - начать новую игру\n"
        "   /stop - завершить текущую игру\n"
        "3. HTML-игры:\n"
        "   /heartgame - открыть игру с сердечками\n"
        "   /webtetris - открыть веб-версию тетриса\n\n"
        "🎮 Управление в тетрисе:\n"
        "← → - перемещение фигуры\n"
        "↓ - ускорить падение\n"
        "↻ - поворот фигуры\n"
        "⏏️ - мгновенное падение\n"
        "⏯ - пауза/продолжить"
    )

# ===== ОТПРАВКА ССЫЛОК НА HTML-ФАЙЛЫ =====
async def show_heart_game(update: Update, context: CallbackContext) -> None:
    try:
        await update.message.reply_text(
            f"🎮 Игра с сердечками:\n{HEART_GAME_URL}",
            disable_web_page_preview=True
        )
        logger.info(f"Отправлена ссылка на hearts.html: {HEART_GAME_URL}")
    except Exception as e:
        logger.error(f"Ошибка при отправке ссылки: {e}")
        await update.message.reply_text("Произошла ошибка при отправке ссылки")

async def show_web_tetris(update: Update, context: CallbackContext) -> None:
    try:
        await update.message.reply_text(
            f"🎮 Веб-версия тетриса:\n{TETRIS_GAME_URL}",
            disable_web_page_preview=True
        )
        logger.info(f"Отправлена ссылка на tetris.html: {TETRIS_GAME_URL}")
    except Exception as e:
        logger.error(f"Ошибка при отправке ссылки: {e}")
        await update.message.reply_text("Произошла ошибка при отправке ссылки")

# ===== ОБРАБОТЧИКИ ТЕТРИСА =====
async def start_tetris(update: Update, context: CallbackContext) -> None:
    chat_id = update.effective_chat.id
    games[chat_id] = Tetris()
    await send_tetris_board(update, context)

async def stop_tetris(update: Update, context: CallbackContext) -> None:
    chat_id = update.effective_chat.id
    if chat_id in games:
        del games[chat_id]
        await update.message.reply_text("Игра завершена!")
    else:
        await update.message.reply_text("Активная игра не найдена.")

async def send_tetris_board(update: Update, context: CallbackContext, is_callback=False):
    chat_id = update.effective_chat.id

    # Создаем новую игру, если нужно
    if chat_id not in games:
        games[chat_id] = Tetris()

    tetris = games[chat_id]

    # Создаем клавиатуру управления
    keyboard = [
        [
            InlineKeyboardButton("←", callback_data="left"),
            InlineKeyboardButton("↓", callback_data="down"),
            InlineKeyboardButton("→", callback_data="right")
        ],
        [
            InlineKeyboardButton("↻ Поворот", callback_data="rotate"),
            InlineKeyboardButton("⏏️ Падение", callback_data="drop")
        ],
        [
            InlineKeyboardButton("⏯ Пауза", callback_data="pause"),
            InlineKeyboardButton("🔄 Новая игра", callback_data="new"),
            InlineKeyboardButton("❌ Выход", callback_data="stop")
        ]
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    # Получаем изображение и текст состояния
    board_img = tetris.get_board_image()
    text = tetris.get_state_text()

    # Отправляем/обновляем сообщение
    if is_callback:
        query = update.callback_query
        await query.message.edit_media(
            media=InputMediaPhoto(media=board_img, caption=text),
            reply_markup=reply_markup
        )
        await query.answer()
    else:
        if 'tetris_message' in context.chat_data:
            try:
                await context.bot.delete_message(chat_id, context.chat_data['tetris_message'])
            except:
                pass

        message = await context.bot.send_photo(
            chat_id=chat_id,
            photo=board_img,
            caption=text,
            reply_markup=reply_markup
        )
        context.chat_data['tetris_message'] = message.message_id

async def button_handler(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    chat_id = query.message.chat_id
    data = query.data

    if chat_id not in games:
        await query.answer("Игра не найдена! Начните новую игру /tetris")
        return

    tetris = games[chat_id]

    if data == "left":
        tetris.move(-1, 0)
    elif data == "right":
        tetris.move(1, 0)
    elif data == "down":
        tetris.move(0, 1)
    elif data == "rotate":
        tetris.rotate_piece()
    elif data == "drop":
        while tetris.drop():
            pass
    elif data == "pause":
        tetris.paused = not tetris.paused
    elif data == "new":
        tetris.reset()
    elif data == "stop":
        del games[chat_id]
        await query.message.delete()
        await query.answer("Игра завершена!")
        return

    await send_tetris_board(update, context, is_callback=True)

# ===== ЗАПУСК БОТА =====
def main() -> None:
    application = Application.builder().token(TOKEN).build()

    # Регистрация обработчиков команд
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("tetris", start_tetris))
    application.add_handler(CommandHandler("stop", stop_tetris))
    application.add_handler(CommandHandler("heartgame", show_heart_game))
    application.add_handler(CommandHandler("webtetris", show_web_tetris))

    # Добавляем обработчики из hearts.py
    setup_handlers(application)

    # Обработчик инлайн-кнопок
    application.add_handler(CallbackQueryHandler(button_handler))

    # Запуск бота
    logger.info("Бот запущен и работает...")
    application.run_polling()

if __name__ == "__main__":
    main()
