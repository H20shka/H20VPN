import logging
import sqlite3
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, CallbackQueryHandler

# Включить логирование
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Токен вашего бота (замените на реальный токен из @BotFather)
TOKEN = '8272166182:AAGxnXg-rfFC0s5_fhSCrmISGC6eWDeSrws'

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Отправляет приветственное сообщение при команде /start."""
    if update.message is None:
        return
    welcome_message = (
        "Привет👋\n\n"
        "Мы работаем и наша команда готова освободить Вас от:\n\n"
        "Зависающих видео в запрещённой сети;\n"
        "Бесконечного просмотра рекламы;\n"
        "Блокировки из-за частой смены IP-адреса;\n"
        "Утечки заряда батареи и ваших данных (как у бесплатных VPN)."
    )
    keyboard = [
        [InlineKeyboardButton("Пробный период⌚️", callback_data="trial")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(welcome_message, reply_markup=reply_markup)

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    if query is None:
        return
    await query.answer()

    user_id = query.from_user.id
    username = query.from_user.username or "Unknown"

    conn = sqlite3.connect('vpn_bot.db')
    cursor = conn.cursor()

    # Проверить, есть ли пользователь в базе
    cursor.execute('SELECT trial_used FROM users WHERE user_id = ?', (user_id,))
    result = cursor.fetchone()

    if result is None:
        # Добавить нового пользователя
        cursor.execute('INSERT INTO users (user_id, username, trial_used) VALUES (?, ?, 0)', (user_id, username))
        conn.commit()
        trial_used = 0
    else:
        trial_used = result[0]

    data = query.data

    if data is None:
        return

    if data == "trial":
        if trial_used == 1:
            await query.edit_message_text("Вы уже использовали пробный период.")
        else:
            message = (
                "Ключ выдается едино-разово на 3 дня.\n"
                "Ключ: vless://c570a7a8-9d7e-4434-9269-45589b003857@144.31.120.167:443?type=tcp&encryption=none&security=reality&pbk=D_UlnUhHUnf6TRdDx39c5ew4v_x8rNPLSvD8-ATbEn4&fp=chrome&sni=google.com&sid=fce9aa3bd85c&spx=%2F#H20-lc3vdgu8\n"
                "⬇️Выберите устройство ниже:⬇️"
            )
            keyboard = [
                [InlineKeyboardButton("Android", callback_data="device_android")],
                [InlineKeyboardButton("iOS", callback_data="device_ios")],
                [InlineKeyboardButton("Windows", callback_data="device_windows")],
                [InlineKeyboardButton("Mac", callback_data="device_mac")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(message, reply_markup=reply_markup)
            # Отметить, что пробный период использован
            cursor.execute('UPDATE users SET trial_used = 1 WHERE user_id = ?', (user_id,))
            conn.commit()
    elif data.startswith("device_"):
        device = data.split("_")[1]
        key_message = f"Ключ для {device}: vless://c570a7a8-9d7e-4434-9269-45589b003857@144.31.120.167:443?type=tcp&encryption=none&security=reality&pbk=D_UlnUhHUnf6TRdDx39c5ew4v_x8rNPLSvD8-ATbEn4&fp=chrome&sni=google.com&sid=fce9aa3bd85c&spx=%2F#H20-lc3vdgu8"
        await query.edit_message_text(key_message)

    conn.close()

def main() -> None:
    """Запуск бота."""
    application = ApplicationBuilder().token(TOKEN).build()

    # Добавление обработчика команды /start
    application.add_handler(CommandHandler("start", start))

    # Добавление обработчика callback запросов
    application.add_handler(CallbackQueryHandler(handle_callback))

    # Запуск бота
    application.run_polling()

if __name__ == '__main__':
    main()
