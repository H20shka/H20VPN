import logging
import sqlite3
import time
import requests
import uuid
import json
import asyncio
import random
import base64
import nest_asyncio
from cryptography.hazmat.primitives.asymmetric import x25519
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, CallbackQueryHandler
from telegram.error import BadRequest

nest_asyncio.apply()

# Включить логирование
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Токен вашего бота (замените на реальный токен из @BotFather)
TOKEN = '8272166182:AAGxnXg-rfFC0s5_fhSCrmISGC6eWDeSrws'

# ID канала для проверки подписки
CHANNEL_ID = '@H20_shop1'

# Список админов (добавьте свои user_id)
ADMINS = [863968972, 551107612]

def create_trial_inbound(user_id):
    try:
        base_url = "http://144.31.120.167:54321/dvoykinsecretpanel"
        login_url = f"{base_url}/login"
        login_data = {"username": "H20shka", "password": "aH0908bH?!"}
        session = requests.Session()
        response = session.post(login_url, data=login_data)

        # Проверить существующие inbound для пользователя
        list_url = f"{base_url}/panel/api/inbounds/list"
        response = session.get(list_url)
        if response.status_code == 200:
            try:
                inbounds_response = response.json()
                if inbounds_response.get('success') and inbounds_response.get('obj'):
                    for inbound in inbounds_response['obj']:
                        if inbound.get('remark') == f"H2O_{user_id}":
                            if inbound.get('enable') and inbound.get('expiryTime', 0) > time.time() * 1000:
                                # Найден активный inbound, извлечь ключ
                                settings_str = inbound.get('settings')
                                if settings_str:
                                    try:
                                        settings = json.loads(settings_str)
                                        clients = settings.get('clients', [])
                                        if clients:
                                            client_id = clients[0].get('id')
                                            port = inbound.get('port')
                                            stream_settings_str = inbound.get('streamSettings')
                                            if stream_settings_str:
                                                stream_settings = json.loads(stream_settings_str)
                                                reality_settings = stream_settings.get('realitySettings', {})
                                                inner_settings = reality_settings.get('settings', {})
                                                public_key = inner_settings.get('publicKey')
                                                if client_id and port and public_key:
                                                    server = "144.31.120.167"
                                                uri = f"vless://{client_id}@{server}:{port}?type=tcp&encryption=none&security=reality&pbk={public_key}&fp=chrome&sni=google.com&sid={stream_settings['realitySettings']['shortIds'][0]}&spx=%2F#H2O"
                                                return uri
                                    except json.JSONDecodeError:
                                        pass
                            else:
                                # Найден истекший inbound, извлечь ключ и вернуть сообщение активации
                                settings_str = inbound.get('settings')
                                if settings_str:
                                    try:
                                        settings = json.loads(settings_str)
                                        clients = settings.get('clients', [])
                                        if clients:
                                            client_id = clients[0].get('id')
                                            port = inbound.get('port')
                                            stream_settings_str = inbound.get('streamSettings')
                                            if stream_settings_str:
                                                stream_settings = json.loads(stream_settings_str)
                                                reality_settings = stream_settings.get('realitySettings', {})
                                                inner_settings = reality_settings.get('settings', {})
                                                public_key = inner_settings.get('publicKey')
                                                if client_id and port and public_key:
                                                    server = "144.31.120.167"
                                                    uri = f"vless://{client_id}@{server}:{port}?type=tcp&encryption=none&security=reality&pbk={public_key}&fp=chrome&sni=google.com&sid={stream_settings['realitySettings']['shortIds'][0]}&spx=%2F#H2O"
                                                    return uri
                                    except json.JSONDecodeError:
                                        pass
            except json.JSONDecodeError:
                pass

        # Если не найден активный, создать новый
        client_id = str(uuid.uuid4())
        port = random.randint(10000, 25000)

        # Генерация ключей X25519 для Reality
        private_key = x25519.X25519PrivateKey.generate()
        public_key_b64 = base64.urlsafe_b64encode(private_key.public_key().public_bytes_raw()).decode().rstrip('=')
        private_key_b64 = base64.urlsafe_b64encode(private_key.private_bytes_raw()).decode().rstrip('=')

        settings = {
            "clients": [
                {
                    "id": client_id,
                    "flow": "xtls-rprx-vision",
                    "email": f"user{user_id}_{int(time.time())}@gmail.com",
                    "limitIp": 0,
                    "totalGB": 0,
                    "expiryTime": int((time.time() + 259200) * 1000),
                    "enable": True,
                    "tgId": str(user_id),
                    "subId": ""
                }
            ],
            "decryption": "none",
            "fallbacks": []
        }

        stream_settings = {
            "network": "tcp",
            "security": "reality",
            "realitySettings": {
                "show": False,
                "xver": 0,
                "dest": "google.com:443",
                "serverNames": ["google.com", "www.google.com"],
                "privateKey": private_key_b64,
                "minClient": "25.9.11",
                "maxClient": "25.9.11",
                "maxTimediff": 0,
                "shortIds": [f"{random.randint(0, 0xFFFFFFFF):08x}"],
                "settings": {
                    "publicKey": public_key_b64,
                    "fingerprint": "chrome",
                    "serverName": "google.com",
                    "spiderX": "/"
                }
            },
            "tcpSettings": {
                "acceptProxyProtocol": False,
                "header": {
                    "type": "none"
                }
            }
        }

        sniffing = {
            "enabled": True,
            "destOverride": ["http", "tls", "quic"]
        }

        inbound_data = {
            "up": 0,
            "down": 0,
            "total": 0,
            "remark": f"H2O_{user_id}",
            "enable": True,
            "expiryTime": int((time.time() + 259200) * 1000),
            "listen": "",
            "port": port,
            "protocol": "vless",
            "settings": json.dumps(settings),
            "streamSettings": json.dumps(stream_settings),
            "sniffing": json.dumps(sniffing)
        }

        create_url = f"{base_url}/panel/api/inbounds/add"
        response = session.post(create_url, json=inbound_data)

        if response.status_code == 200:
            try:
                inbound_response = response.json()
                if not isinstance(inbound_response, dict):
                    return f"Ошибка: некорректный ответ от API: {inbound_response}"
            except json.JSONDecodeError:
                return f"Ошибка: ответ не является JSON: {response.text}"
            if inbound_response.get('success') and inbound_response.get('obj'):
                # Генерация полного Vless URI с заранее сгенерированными ключами
                server = "144.31.120.167"
                uri = f"vless://{client_id}@{server}:{port}?type=tcp&encryption=none&security=reality&pbk={public_key_b64}&fp=chrome&sni=google.com&sid={stream_settings['realitySettings']['shortIds'][0]}&spx=%2F#H2O"

                return uri
            else:
                return f"Ошибка создания инбаунда: {inbound_response}"
        else:
            return f"Ошибка создания инбаунда: {response.status_code} {response.text}"
    except Exception as e:
        return f"Ошибка: {str(e)}"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Отправляет приветственное сообщение при команде /start."""
    if update.message is None:
        return

    user_id = update.message.from_user.id

    # Проверить блокировку
    conn = sqlite3.connect('vpn_bot.db')
    cursor = conn.cursor()
    cursor.execute("SELECT banned FROM users WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    if row and row[0] == 1:
        await update.message.reply_text("Вы заблокированы.")
        return

    await update.message.reply_text("Привет👋")

    info_message = (
        "🔋Мы работаем и наша команда готова освободить Вас от:\n\n"
        "⌛️Зависающих видео в запрещённой сети;\n"
        "📲Бесконечного просмотра рекламы;\n"
        "❌Блокировки из-за частой смены IP-адреса;\n"
        "🪫Утечки заряда батареи и ваших данных (как у бесплатных VPN)."
    )
    await update.message.reply_text(info_message)

    # Проверить подписку на канал
    try:
        member = await context.bot.get_chat_member(chat_id=CHANNEL_ID, user_id=user_id)
        if member.status not in ['member', 'administrator', 'creator']:
            keyboard = [
                [InlineKeyboardButton("Подписаться✅", url="https://t.me/H20_shop1")],
                [InlineKeyboardButton("Проверить подписку", callback_data="check_sub")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text("Для использования бота подпишитесь на наш канал.", reply_markup=reply_markup)
            return
    except BadRequest:
        await update.message.reply_text("Не удалось проверить подписку на канал.")
        return

    keyboard = [
        [InlineKeyboardButton("Пробный период⌚️", callback_data="trial")],
        [InlineKeyboardButton("О сервисе📊", callback_data="about")],
        [InlineKeyboardButton("Помощь🆘", callback_data="help")]
    ]
    if user_id in ADMINS:
        keyboard.insert(0, [InlineKeyboardButton("Админка", callback_data="admin")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("⬇️Выберите опцию из доступных ниже:⬇️", reply_markup=reply_markup)
    # Добавить пользователя в базу
    conn = sqlite3.connect('vpn_bot.db')
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO users (user_id) VALUES (?)", (update.message.from_user.id,))
    conn.commit()
    conn.close()

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    if query is None:
        return
    await query.answer()

    user_id = query.from_user.id
    data = query.data

    if data == "trial":
        # Проверить статус пробного периода
        conn = sqlite3.connect('vpn_bot.db')
        cursor = conn.cursor()
        cursor.execute("SELECT trial_used, subscription_expiry FROM users WHERE user_id = ?", (user_id,))
        row = cursor.fetchone()
        conn.close()
        current_time = time.time()
        if row:
            trial_used, subscription_expiry = row
            if trial_used == 0:
                # Не активирован, предложить активировать
                keyboard = [
                    [InlineKeyboardButton("Активировать пробный период⌚️", callback_data="activate_trial")],
                    [InlineKeyboardButton("Вернуться в главное меню", callback_data="back")]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                await query.edit_message_text("Пробный период не активирован. Хотите активировать?", reply_markup=reply_markup)
            elif subscription_expiry > current_time:
                # Активен, показать оставшееся время
                remaining = int(subscription_expiry - current_time)
                days = remaining // 86400
                hours = (remaining % 86400) // 3600
                minutes = (remaining % 3600) // 60
                message = f"Пробный период активен. Осталось времени: {days} дней {hours} часов {minutes} минут."
                keyboard = [[InlineKeyboardButton("Вернуться в главное меню", callback_data="back")]]
                reply_markup = InlineKeyboardMarkup(keyboard)
                await query.edit_message_text(message, reply_markup=reply_markup)
            else:
                # Истек
                message = "Ваш пробный период закончился."
                keyboard = [[InlineKeyboardButton("Вернуться в главное меню", callback_data="back")]]
                reply_markup = InlineKeyboardMarkup(keyboard)
                await query.edit_message_text(message, reply_markup=reply_markup)
        else:
            # Пользователь не найден, но это маловероятно
            await query.edit_message_text("Ошибка: пользователь не найден.")
    elif data == "activate_trial":
        # Активировать пробный период
        conn = sqlite3.connect('vpn_bot.db')
        cursor = conn.cursor()
        cursor.execute("SELECT trial_used FROM users WHERE user_id = ?", (user_id,))
        row = cursor.fetchone()
        if row and row[0] == 1:
            await query.edit_message_text("Вы уже использовали пробный период.")
            conn.close()
            return
        # Создать инбаунд
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, create_trial_inbound, user_id)
        if result.startswith("vless://"):
            # Обновить базу данных
            expiry_time = int(time.time() + 259200)
            cursor.execute("UPDATE users SET trial_used = 1, subscription_expiry = ?, trial_notification_sent = 0 WHERE user_id = ?", (expiry_time, user_id))
            conn.commit()
            conn.close()
            message = f"🟢Ключ выдается едино-разово на 3 дня🟢\n🔴Ключ: {result}\n⬇️Выберите устройство ниже:⬇️"
            keyboard = [
                [InlineKeyboardButton("Скопировать ключ", copy_text={"text": result})],
                [InlineKeyboardButton("iOs📱", callback_data="ios"), InlineKeyboardButton("Android📱", callback_data="android")],
                [InlineKeyboardButton("MacOs💻", callback_data="macos"), InlineKeyboardButton("Windows🖥", callback_data="windows")],
                [InlineKeyboardButton("Linux💻", callback_data="linux")],
                [InlineKeyboardButton("Вернуться в главное меню", callback_data="back")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(message, reply_markup=reply_markup)
        else:
            conn.close()
            await query.edit_message_text(result)
    elif data == "ios":
        message = "Скачать приложение можно выбрав снизу подходящию версию iOs и нажав на нужную кнопку⬇️\nДля активации зайдите в приложение и скопировав ключ, нажмите добавить из буфера обмена."
        keyboard = [
            [InlineKeyboardButton("Для пользователей с iOs 16 и выше🟡", url="https://apps.apple.com/ru/app/v2raytun/id6476628951")],
            [InlineKeyboardButton("Для пользователей с iOs до 16🟢", url="https://apps.apple.com/ru/app/v2box-v2ray-client/id6446814690")],
            [InlineKeyboardButton("Вернуться в главное меню", callback_data="back")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(message, reply_markup=reply_markup)
    elif data == "android":
        message = "Скачать приложение можно ниже по нажатию на кнопку⬇️\nДля активации зайдите в приложение и скопировав ключ, нажмите добавить из буфера обмена"
        keyboard = [
            [InlineKeyboardButton("Скачать для Android🟠", url="https://play.google.com/store/apps/details?id=com.v2raytun.android&pcampaignid=web_share")],
            [InlineKeyboardButton("Вернуться в главное меню", callback_data="back")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(message, reply_markup=reply_markup)
    elif data == "macos":
        message = "Скачать приложение можно ниже по нажатию на кнопку⬇️\nДля активации зайдите в приложение и скопировав ключ, нажмите добавить из буфера обмена"
        keyboard = [
            [InlineKeyboardButton("Скачать для MacOs💻", url="https://apps.apple.com/us/app/v2raytun/id6476628951?platform=mac")],
            [InlineKeyboardButton("Вернуться в главное меню", callback_data="back")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(message, reply_markup=reply_markup)
    elif data == "windows":
        message = "Скачать приложение можно ниже по нажатию на кнопку⬇️\nДля активации зайдите в приложение и скопировав ключ, нажмите добавить из буфера обмена"
        keyboard = [
            [InlineKeyboardButton("Скачать для Windows🖥", url="https://github.com/hiddify/hiddify-app/releases/latest/download/Hiddify-Windows-Setup-x64.Msix")],
            [InlineKeyboardButton("Вернуться в главное меню", callback_data="back")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(message, reply_markup=reply_markup)
    elif data == "linux":
        message = "Скачать приложение можно ниже по нажатию на кнопку⬇️\nДля активации зайдите в приложение и скопировав ключ, нажмите добавить из буфера обмена"
        keyboard = [
            [InlineKeyboardButton("Скачать для Linux💻", url="https://github.com/hiddify/hiddify-app/releases/latest/download/Hiddify-Linux-x64.AppImage")],
            [InlineKeyboardButton("Вернуться в главное меню", callback_data="back")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(message, reply_markup=reply_markup)
    elif data == "help":
        message = (
            "Возникли вопросы❓❗️\n"
            "Напиши нам и мы поможем со всем✅\n"
            "Пиши: @H20tag"
        )
        keyboard = [[InlineKeyboardButton("Вернуться в главное меню", callback_data="back")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(message, reply_markup=reply_markup)
    elif data == "about":
        conn = sqlite3.connect('vpn_bot.db')
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM users")
        active_users = cursor.fetchone()[0]
        conn.close()
        message = (
            "Мы предоставляем VPN с самой высокой скоростью и комфортной настройкой за считанные секунды.\n\n"
            f"Количество активных пользователей-{active_users}🧮;\n"
            "Сколько мы уже работаем-мы работаем для вас каждый день с 02.11.2025🗓;\n"
            "Активная поддержка 24/7📩;\n"
            "Высокая скорость и доступность нескольких локаций🏎;"
        )
        keyboard = [[InlineKeyboardButton("Вернуться в главное меню", callback_data="back")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(message, reply_markup=reply_markup)
    elif data == "check_sub":
        # Проверить подписку
        try:
            member = await context.bot.get_chat_member(chat_id=CHANNEL_ID, user_id=user_id)
            if member.status not in ['member', 'administrator', 'creator']:
                keyboard = [
                    [InlineKeyboardButton("Подписаться✅", url="https://t.me/H20_shop1")],
                    [InlineKeyboardButton("Проверить подписку", callback_data="check_sub")]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                await query.edit_message_text("Вы не подписаны на канал. Для использования бота подпишитесь на наш канал.", reply_markup=reply_markup)
            else:
                keyboard = [
                    [InlineKeyboardButton("Пробный период⌚️", callback_data="trial")],
                    [InlineKeyboardButton("О сервисе📊", callback_data="about")],
                    [InlineKeyboardButton("Помощь🆘", callback_data="help")]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                await query.edit_message_text("Подписка проверена! Выберите опцию:", reply_markup=reply_markup)
        except BadRequest:
            await query.edit_message_text("Не удалось проверить подписку на канал.")
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
            [InlineKeyboardButton("Пробный период⌚️", callback_data="trial")],
            [InlineKeyboardButton("О сервисе📊", callback_data="about")],
            [InlineKeyboardButton("Помощь🆘", callback_data="help")]
        ]
        if user_id in ADMINS:
            keyboard.insert(0, [InlineKeyboardButton("Админка", callback_data="admin")])
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(welcome_message, reply_markup=reply_markup)
    elif data == "admin":
        if user_id not in ADMINS:
            return
        keyboard = [
            [InlineKeyboardButton("Просмотр пользователей", callback_data="admin_users")],
            [InlineKeyboardButton("Заблокировать пользователя", callback_data="admin_ban")],
            [InlineKeyboardButton("Анулировать подписку", callback_data="admin_cancel")],
            [InlineKeyboardButton("Вернуться в главное меню", callback_data="back")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text("Админ меню:", reply_markup=reply_markup)
    elif data == "admin_users":
        if user_id not in ADMINS:
            return
        conn = sqlite3.connect('vpn_bot.db')
        cursor = conn.cursor()
        cursor.execute("SELECT user_id, trial_used, subscription_expiry, banned FROM users")
        rows = cursor.fetchall()
        conn.close()
        message = "Пользователи:\n"
        for row in rows:
            status = "Заблокирован" if row[3] else ("Активен" if row[2] > time.time() else "Неактивен")
            message += f"ID: {row[0]}, Trial: {'Да' if row[1] else 'Нет'}, Status: {status}\n"
        await query.edit_message_text(message[:4000], reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Вернуться в главное меню", callback_data="back")]]))
    elif data == "admin_ban":
        if user_id not in ADMINS:
            return
        await query.edit_message_text("Введите команду /ban <user_id> для блокировки.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Вернуться в главное меню", callback_data="back")]]))
    elif data == "admin_cancel":
        if user_id not in ADMINS:
            return
        await query.edit_message_text("Введите команду /cancel <user_id> для анулирования подписки.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Вернуться в главное меню", callback_data="back")]]))

async def ban_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message.from_user.id not in ADMINS:
        await update.message.reply_text("У вас нет прав.")
        return
    if not context.args:
        await update.message.reply_text("Использование: /ban <user_id>")
        return
    try:
        target_id = int(context.args[0])
    except ValueError:
        await update.message.reply_text("Неверный user_id")
        return
    conn = sqlite3.connect('vpn_bot.db')
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET banned = 1 WHERE user_id = ?", (target_id,))
    conn.commit()
    conn.close()
    await update.message.reply_text(f"Пользователь {target_id} заблокирован.")

async def unban_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message.from_user.id not in ADMINS:
        await update.message.reply_text("У вас нет прав.")
        return
    if not context.args:
        await update.message.reply_text("Использование: /unban <user_id>")
        return
    try:
        target_id = int(context.args[0])
    except ValueError:
        await update.message.reply_text("Неверный user_id")
        return
    conn = sqlite3.connect('vpn_bot.db')
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET banned = 0 WHERE user_id = ?", (target_id,))
    conn.commit()
    conn.close()
    await update.message.reply_text(f"Пользователь {target_id} разблокирован.")

async def cancel_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message.from_user.id not in ADMINS:
        await update.message.reply_text("У вас нет прав.")
        return
    if not context.args:
        await update.message.reply_text("Использование: /cancel <user_id>")
        return
    try:
        target_id = int(context.args[0])
    except ValueError:
        await update.message.reply_text("Неверный user_id")
        return
    conn = sqlite3.connect('vpn_bot.db')
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET subscription_expiry = 0 WHERE user_id = ?", (target_id,))
    conn.commit()
    conn.close()
    await update.message.reply_text(f"Подписка пользователя {target_id} анулирована.")

async def users_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message.from_user.id not in ADMINS:
        await update.message.reply_text("У вас нет прав.")
        return
    conn = sqlite3.connect('vpn_bot.db')
    cursor = conn.cursor()
    cursor.execute("SELECT user_id, trial_used, subscription_expiry, banned FROM users")
    rows = cursor.fetchall()
    conn.close()
    message = "Пользователи:\n"
    for row in rows:
        status = "Заблокирован" if row[3] else ("Активен" if row[2] > time.time() else "Неактивен")
        message += f"ID: {row[0]}, Trial: {'Да' if row[1] else 'Нет'}, Status: {status}\n"
    await update.message.reply_text(message[:4000])

async def check_trial_expiry(application):
    """Проверяет истекшие пробные периоды и отправляет уведомления."""
    while True:
        conn = sqlite3.connect('vpn_bot.db')
        cursor = conn.cursor()
        cursor.execute("SELECT user_id FROM users WHERE subscription_expiry > 0 AND subscription_expiry < ? AND trial_notification_sent = 0", (time.time(),))
        expired_users = cursor.fetchall()
        for (user_id,) in expired_users:
            try:
                await application.bot.send_message(chat_id=user_id, text="Ваш пробный период закончился. Для продолжения приобретите подписку.")
                cursor.execute("UPDATE users SET trial_notification_sent = 1 WHERE user_id = ?", (user_id,))
            except Exception as e:
                logger.error(f"Не удалось отправить сообщение пользователю {user_id}: {e}")
        conn.commit()
        conn.close()
        await asyncio.sleep(3600)  # Проверка каждый час

async def main() -> None:
    """Запуск бота."""
    # Создание таблицы пользователей, если не существует
    conn = sqlite3.connect('vpn_bot.db')
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        trial_used INTEGER DEFAULT 0,
        subscription_expiry INTEGER DEFAULT 0,
        trial_notification_sent INTEGER DEFAULT 0,
        banned INTEGER DEFAULT 0
    )''')
    # Add columns if not exists
    try:
        cursor.execute("ALTER TABLE users ADD COLUMN trial_notification_sent INTEGER DEFAULT 0")
    except sqlite3.OperationalError:
        pass
    try:
        cursor.execute("ALTER TABLE users ADD COLUMN banned INTEGER DEFAULT 0")
    except sqlite3.OperationalError:
        pass
    conn.commit()
    conn.close()

    application = ApplicationBuilder().token(TOKEN).build()

    # Добавление обработчика команды /start
    application.add_handler(CommandHandler("start", start))

    # Добавление обработчика callback запросов
    application.add_handler(CallbackQueryHandler(handle_callback))

    # Добавление админ команд
    application.add_handler(CommandHandler("ban", ban_command))
    application.add_handler(CommandHandler("unban", unban_command))
    application.add_handler(CommandHandler("cancel", cancel_command))
    application.add_handler(CommandHandler("users", users_command))

    # Запустить фоновую задачу для проверки истекших пробных периодов
    asyncio.create_task(check_trial_expiry(application))

    # Запуск бота
    await application.run_polling()

if __name__ == '__main__':
    asyncio.run(main())
