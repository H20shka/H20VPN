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
    data = query.data

    conn = sqlite3.connect('vpn_bot.db')
    cursor = conn.cursor()

    if data == "trial":
        cursor.execute("SELECT trial_used FROM users WHERE user_id = ?", (user_id,))
        result = cursor.fetchone()
        if result and result[0] == 1:
            await query.edit_message_text("Вы уже использовали пробный период.")
        else:
            message = (
                "Ключ выдается едино-разово на 3 дня.\n"
                "Ключ: vless://c570a7a8-9d7e-4434-9269-45589b003857@144.31.120.167:443?type=tcp&encryption=none&security=reality&pbk=D_UlnUhHUnf6TRdDx39c5ew4v_x8rNPLSvD8-ATbEn4&fp=chrome&sni=google.com&sid=fce9aa3bd85c&spx=%2F#H20-lc3vdgu8\n"
                "⬇️Выберите устройство ниже:⬇️"
            )
            keyboard = [
                [InlineKeyboardButton("iOs", callback_data="ios"), InlineKeyboardButton("Android", callback_data="android")],
                [InlineKeyboardButton("MacOs", callback_data="macos"), InlineKeyboardButton("Windows", callback_data="windows")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(message, reply_markup=reply_markup)
            cursor.execute("INSERT OR REPLACE INTO users (user_id, trial_used) VALUES (?, 1)", (user_id,))
            conn.commit()
    elif data == "ios":
        message = (
            "Скачать приложение:\n"
            "Для пользователей с iOs 16 и выше : https://apps.apple.com/ru/app/v2raytun/id6476628951\n"
            "Для пользователей с iOs до 16 : https://apps.apple.com/ru/app/v2box-v2ray-client/id6446814690\n"
            "Для активации зайдите в приложение и скопировав ключ,нажмите добавить из буфера обмена"
        )
        keyboard = [[InlineKeyboardButton("Вернуться в главное меню", callback_data="back")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(message, reply_markup=reply_markup)
    elif data == "android":
        message = (
            "Скачать приложение: https://play.google.com/store/apps/details?id=com.v2raytun.android&pcampaignid=web_share\n"
            "Для активации зайдите в приложение и скопировав ключ,нажмите добавить из буфера обмена"
        )
        keyboard = [[InlineKeyboardButton("Вернуться в главное меню", callback_data="back")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(message, reply_markup=reply_markup)
    elif data == "macos":
        message = (
            "Скачать приложение: https://apps.apple.com/us/app/v2raytun/id6476628951?platform=mac\n"
            "Для активации зайдите в приложение и скопировав ключ,нажмите добавить из буфера обмена"
        )
        keyboard = [[InlineKeyboardButton("Вернуться в главное меню", callback_data="back")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(message, reply_markup=reply_markup)
    elif data == "windows":
        message = (
            "Скачать приложение: https://github.com/hiddify/hiddify-app/releases/latest/download/Hiddify-Windows-Setup-x64.Msix\n"
            "Для активации зайдите в приложение и скопировав ключ,нажмите добавить из буфера обмена"
        )
        keyboard = [[InlineKeyboardButton("Вернуться в главное меню", callback_data="back")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(message, reply_markup=reply_markup)
    elif data == "back":
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
        await query.edit_message_text(welcome_message, reply_markup=reply_markup)

    conn.close()

def main() -> None:
    """Запуск бота."""
    # Создание таблицы пользователей, если не существует
    conn = sqlite3.connect('vpn_bot.db')
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        trial_used INTEGER DEFAULT 0
    )''')
    conn.commit()
    conn.close()

    application = ApplicationBuilder().token(TOKEN).build()

    # Добавление обработчика команды /start
    application.add_handler(CommandHandler("start", start))

    # Добавление обработчика callback запросов
    application.add_handler(CallbackQueryHandler(handle_callback))

    # Запуск бота
    application.run_polling()

if __name__ == '__main__':
    main()
