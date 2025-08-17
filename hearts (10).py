import random
from telegram import Update
from telegram.ext import CallbackContext, CommandHandler
import os
import json
from typing import Dict, Any, Union

# Конфигурация
MAIN_ADMIN = "Mikilyt"  # Главный администратор
USER_DATA_FILE = "user_relations.json"
ADMIN_DATA_FILE = "admin_data.json"

# Коды доступа
ACCESS_CODES = {
    "7843": {"name": "girlfriend", "emoji": "💖", "title": "Девушка"},
    "9486": {"name": "sister", "emoji": "👩‍❤️‍👩", "title": "Сестра"},
    "3642": {"name": "mother", "emoji": "👩‍👧", "title": "Мама"},
    "5829": {"name": "friend", "emoji": "🤝", "title": "Подруга"}
}

# Базовый шаблон сердечка
HEART_TEMPLATE = """
_______{0}{0}{0}__{0}{0}{0}
_____{0}{0}{0}{0}{0}{0}{0}{0}{0}  
____{0}{0}{0}{0}{0}{0}{0}{0}{0}{0}
____{0}{0}{0}{0}{0}{0}{0}{0}{0}{0}
______{0}{0}{0}{0}{0}{0}{0}{0}  
_______-{0}{0}{0}{0}{0}{0}   
__________-{0}{0}{0}{0}
____________-{0}{0}
______________{0}
(\__/)  
(•ㅅ•)  
/ 　 づ{0}♡ {1}
"""

# Разные типы сердечек
HEART_TYPES = {
    "girlfriend": ["❤️", "💖", "💜", "💗", "💓", "💞"],
    "sister": ["💙", "💜", "💖", "💗", "💞"],
    "mother": ["❤️", "💖", "🧡", "💛"],
    "friend": ["💚", "💙", "💜", "🤍"]
}

# Случайные подписи
SIGNATURES = {
    "girlfriend": [
        "Люблю тебя больше всего на свете!",
        "Ты самая лучшая!",
        "Моя любимая!",
        "Для тебя, моя половинка!",
        "С любовью от меня!"
    ],
    "sister": [
        "Держи, сестрёнка, я сделал это для тебя",
        "Лови мои сердечки, сестра!",
        "Сердечки специально для тебя!",
        "Для самой лучшей сестры!",
        "Ты заслуживаешь все сердечки мира!"
    ],
    "mother": [
        "Лучшей маме на свете!",
        "Спасибо за всё, мама!",
        "Люблю тебя, мамочка!",
        "Для самой дорогой!",
        "Ты - самое дорогое, что у меня есть!"
    ],
    "friend": [
        "Лучшей подруге!",
        "Спасибо за дружбу!",
        "Для самой верной подруги!",
        "Друзья навсегда!",
        "Ты - самая лучшая!"
    ]
}

# Цвета для HTML оформления
HEART_COLORS = [
    "#FF0000",  # Красный
    "#FF69B4",  # Розовый
    "#9370DB",  # Фиолетовый
    "#1E90FF",  # Голубой
    "#32CD32",  # Зеленый
    "#FFD700",  # Желтый
    "#FF8C00",  # Оранжевый
    "#FFFFFF",  # Белый
    "#FF1493",  # Ярко-розовый
    "#FF4500",  # Оранжево-красный
    "#DA70D6"   # Орхидея
]

def load_data(filename: str) -> Dict[str, Any]:
    """Загружает данные из JSON файла с автоматическим преобразованием формата"""
    if os.path.exists(filename):
        try:
            with open(filename, "r", encoding='utf-8') as f:
                data = json.load(f)
                # Конвертация старого формата в новый
                new_data = {}
                for key, value in data.items():
                    if isinstance(value, str):  # Старый формат: "user_id": "relation"
                        new_data[key] = {"relation": value, "username": None}
                    else:  # Новый формат: "user_id": {"relation": "...", "username": "..."}
                        new_data[key] = value
                return new_data
        except (json.JSONDecodeError, IOError) as e:
            print(f"Ошибка загрузки данных: {e}")
            return {}
    return {}

def save_data(data: Dict[str, Any], filename: str) -> bool:
    """Сохраняет данные в JSON файл"""
    try:
        with open(filename, "w", encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except IOError as e:
        print(f"Ошибка сохранения данных: {e}")
        return False

def is_admin(username: str) -> bool:
    """Проверяет администраторские права"""
    if not username:
        return False
    admin_data = load_data(ADMIN_DATA_FILE)
    return (username.lower() == MAIN_ADMIN.lower() or 
            username.lower() in [a.lower() for a in admin_data.get("admins", [])])

async def find_user_relation(user_id: str, username: str) -> Union[str, None]:
    """Находит отношения пользователя по ID или username"""
    user_data = load_data(USER_DATA_FILE)

    # 1. Поиск по user_id
    if user_id in user_data:
        return user_data[user_id]["relation"]

    # 2. Поиск по username (если есть)
    if username:
        # Проверяем все записи на совпадение username
        for data in user_data.values():
            if data.get("username", "").lower() == username.lower():
                return data["relation"]

        # Проверяем ключи вида "username_xxx"
        username_key = f"username_{username.lower()}"
        if username_key in user_data:
            return user_data[username_key]["relation"]

    return None

async def start_love(update: Update, context: CallbackContext) -> None:
    """Обработчик команды /love"""
    user_id = str(update.effective_user.id)
    username = update.effective_user.username
    relation = await find_user_relation(user_id, username)

    if not relation:
        await update.message.reply_text("❌ Ваши отношения не установлены. Обратитесь к администратору.")
        return

    if relation not in HEART_TYPES:
        await update.message.reply_text("❌ Ваш тип отношений не распознан. Обратитесь к администратору.")
        return

    try:
        # Выбираем случайный тип сердечка, подпись и цвет
        heart_type = random.choice(HEART_TYPES[relation])
        signature = random.choice(SIGNATURES[relation])
        color = random.choice(HEART_COLORS)

        # Создаем сердечко
        heart_art = HEART_TEMPLATE.format(heart_type, signature)

        # Форматируем сообщение с цветом
        message = f'<pre style="color: {color};">{heart_art}</pre>'

        await update.message.reply_text(
            text=message,
            parse_mode='HTML'
        )
    except Exception as e:
        await update.message.reply_text("❌ Произошла ошибка при создании сердечка.")

async def set_user_relation(update: Update, context: CallbackContext) -> None:
    """Устанавливает отношения для пользователя"""
    if not is_admin(update.message.from_user.username):
        await update.message.reply_text("❌ Недостаточно прав.")
        return

    if len(context.args) < 2:
        codes_list = "\n".join([f"{code} - {data['title']}" for code, data in ACCESS_CODES.items()])
        await update.message.reply_text(
            f"ℹ️ Использование: /setuser [user_id/username] [код]\n\n"
            f"Доступные коды:\n{codes_list}"
        )
        return

    user_identifier = context.args[0]
    code = context.args[1]

    if code not in ACCESS_CODES:
        await update.message.reply_text("❌ Неверный код отношения.")
        return

    relation = ACCESS_CODES[code]["name"]
    user_data = load_data(USER_DATA_FILE)

    # Определяем ключ для хранения
    if user_identifier.isdigit():  # Это user_id
        storage_key = user_identifier
        username_to_store = None
    else:  # Это username
        storage_key = f"username_{user_identifier.lower()}"
        username_to_store = user_identifier

    # Сохраняем данные
    user_data[storage_key] = {
        "relation": relation,
        "username": username_to_store
    }

    if save_data(user_data, USER_DATA_FILE):
        await update.message.reply_text(
            f"✅ Установлены отношения: {ACCESS_CODES[code]['title']} для "
            f"{'@' + user_identifier if not user_identifier.isdigit() else user_identifier}"
        )
    else:
        await update.message.reply_text("❌ Ошибка сохранения данных.")

async def remove_user_relation(update: Update, context: CallbackContext) -> None:
    """Удаляет отношения пользователя"""
    if not is_admin(update.message.from_user.username):
        await update.message.reply_text("❌ Недостаточно прав.")
        return

    if not context.args:
        await update.message.reply_text("ℹ️ Использование: /removeuser [user_id/username]")
        return

    user_identifier = context.args[0]
    user_data = load_data(USER_DATA_FILE)
    removed = False

    # Удаление по user_id или username
    if user_identifier.isdigit():  # Это user_id
        if user_identifier in user_data:
            del user_data[user_identifier]
            removed = True
    else:  # Это username
        # Удаляем по username в данных
        for key, data in list(user_data.items()):
            if data.get("username", "").lower() == user_identifier.lower():
                del user_data[key]
                removed = True

        # Удаляем по ключу username_xxx
        username_key = f"username_{user_identifier.lower()}"
        if username_key in user_data:
            del user_data[username_key]
            removed = True

    if removed:
        if save_data(user_data, USER_DATA_FILE):
            await update.message.reply_text(f"✅ Отношения для {user_identifier} удалены.")
        else:
            await update.message.reply_text("❌ Ошибка сохранения данных.")
    else:
        await update.message.reply_text(f"ℹ️ Пользователь {user_identifier} не найден.")

async def admin_profile(update: Update, context: CallbackContext) -> None:
    """Показывает админ-панель"""
    if not is_admin(update.message.from_user.username):
        await update.message.reply_text("❌ У вас нет прав администратора.")
        return

    codes_list = "\n".join([f"{code} - {data['title']}" for code, data in ACCESS_CODES.items()])
    message = (
        "👑 <b>Админ-панель</b> 👑\n\n"
        "<b>Команды:</b>\n"
        "/setuser [user_id/username] [код] - установить отношения\n"
        "/removeuser [user_id/username] - удалить отношения\n"
        "/love - отправить сердечко\n\n"
        "<b>Доступные коды:</b>\n"
        f"{codes_list}"
    )
    await update.message.reply_text(message, parse_mode='HTML')

async def my_info(update: Update, context: CallbackContext) -> None:
    """Показывает информацию о текущих отношениях"""
    user_id = str(update.effective_user.id)
    username = update.effective_user.username
    relation = await find_user_relation(user_id, username)

    if relation:
        relation_title = next(
            (v["title"] for v in ACCESS_CODES.values() if v["name"] == relation),
            relation
        )
        await update.message.reply_text(f"ℹ️ Ваши отношения: {relation_title}")
    else:
        await update.message.reply_text("❌ Ваши отношения не установлены.")

def setup_handlers(application):
    """Настраивает обработчики команд"""
    application.add_handler(CommandHandler("love", start_love))
    application.add_handler(CommandHandler("setuser", set_user_relation))
    application.add_handler(CommandHandler("removeuser", remove_user_relation))
    application.add_handler(CommandHandler("helpa", admin_profile))
    application.add_handler(CommandHandler("myinfo", my_info))