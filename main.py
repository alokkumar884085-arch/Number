import os
import time
import logging
import sqlite3
import re
import threading
import requests
import telebot
from telebot import types
from flask import Flask

# ==========================================
# CONFIGURATION
# ==========================================
BOT_TOKEN = "8856008829:AAHgne9V0zbxiSb67FUKNKIQM1x89_Lk1QY"
OWNER_ID = 8785590284

API1_URL = "http://147.135.212.197/crapi/st/viewstats"
API1_TOKEN = "SE5XREZBUzRfTpVnX2dQh3NQcYB2dZBWQ4JpXVxmblp2alCDi25oZg=="

API2_URL = "http://147.135.212.197/crapi/st/viewstats"
API2_TOKEN = "RVdWRElBUzRGcW9WeneNcmd2cGV9ZJd8e29PVlyPcFxeamxSgWVXfw=="

API3_URL = "https://pscall.net/restapi/smsreport"
API3_KEY = "SFNYSj1SS16DgYdyf4KIgA=="

PORT = int(os.environ.get("PORT", 8080))

bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML")
app = Flask(__name__)

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# ==========================================
# COUNTRY MASTER MAP (Code -> Flag, Name)
# ==========================================
COUNTRY_MAP = {
    "IN": ("🇮🇳", "India"),
    "197": ("🇮🇷", "Iran"),
    "61": ("🇧🇫", "Burkina Faso"),
    "901": ("🇲🇿", "Mozambique"),
    "38": ("🇭🇹", "Haiti"),
    "3": ("🇾🇪", "Yemen"),
    "18": ("🇻🇪", "Venezuela"),
    "336": ("🇿🇼", "Zimbabwe"),
    "608": ("🇧🇮", "Burundi"),
    "103": ("🇸🇸", "South Sudan"),
    "2": ("🇪🇬", "Egypt"),
    "117": ("🇹🇯", "Tajikistan"),
    "232": ("🇸🇱", "Sierra Leone"),
    "65": ("🇸🇬", "Singapore"),
    "421": ("🇸🇰", "Slovakia"),
    "386": ("🇸🇮", "Slovenia"),
    "677": ("🇸🇧", "Solomon Islands"),
    "252": ("🇸🇴", "Somalia"),
    "27": ("🇿🇦", "South Africa"),
    "82": ("🇰🇷", "South Korea"),
    "34": ("🇪🇸", "Spain"),
    "94": ("🇱🇰", "Sri Lanka"),
    "249": ("🇸🇩", "Sudan"),
    "597": ("🇸🇷", "Suriname"),
    "268": ("🇸🇿", "Swaziland"),
    "46": ("🇸🇪", "Sweden"),
    "41": ("🇨🇭", "Switzerland"),
    "963": ("🇸🇾", "Syria"),
    "886": ("🇹🇼", "Taiwan"),
    "255": ("🇹🇿", "Tanzania"),
    "66": ("🇹🇭", "Thailand"),
    "670": ("🇹🇱", "Timor-Leste"),
    "228": ("🇹🇬", "Togo"),
    "676": ("🇹🇴", "Tonga"),
    "1868": ("🇹🇹", "Trinidad & Tobago"),
    "216": ("🇹🇳", "Tunisia"),
    "90": ("🇹🇷", "Turkey"),
    "993": ("🇹🇲", "Turkmenistan"),
    "1649": ("🇹🇨", "Turks & Caicos"),
    "688": ("🇹🇻", "Tuvalu"),
    "256": ("🇺🇬", "Uganda"),
    "380": ("🇺🇦", "Ukraine"),
    "971": ("🇦🇪", "UAE"),
    "44": ("🇬🇧", "UK"),
    "598": ("🇺🇾", "Uruguay"),
    "998": ("🇺🇿", "Uzbekistan"),
    "678": ("🇻🇺", "Vanuatu"),
    "84": ("🇻🇳", "Vietnam"),
    "1284": ("🇻🇬", "British Virgin Islands"),
    "1340": ("🇻🇮", "US Virgin Islands"),
    "260": ("🇿🇲", "Zambia"),
    "700": ("🇰🇿", "Kazakhstan"),
    "US": ("🇺🇸", "USA")
}

# ==========================================
# FLASK & KEEP-ALIVE SYSTEM (For Render)
# ==========================================
@app.route('/')
def home():
    return "Bot is alive and running 24/7!", 200

def run_flask():
    app.run(host="0.0.0.0", port=PORT)

def keep_alive_ping():
    while True:
        time.sleep(15)
        try:
            requests.get(f"http://127.0.0.1:{PORT}/", timeout=5)
            logging.info("Ping sent: Bot is active.")
        except Exception as e:
            logging.error(f"Keep-alive ping error: {e}")

# ==========================================
# DATABASE SETUP (SQLite)
# ==========================================
def init_db():
    conn = sqlite3.connect("numbers.db")
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS active_numbers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            number TEXT,
            country TEXT,
            otp_received INTEGER DEFAULT 0,
            otp_text TEXT DEFAULT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS premium_users (
            user_id INTEGER PRIMARY KEY,
            added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    conn.commit()
    conn.close()

init_db()

def add_number_record(user_id, number, country):
    conn = sqlite3.connect("numbers.db")
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO active_numbers (user_id, number, country) VALUES (?, ?, ?)",
        (user_id, number, country)
    )
    conn.commit()
    conn.close()

def mark_otp_received(number, otp_text):
    conn = sqlite3.connect("numbers.db")
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE active_numbers SET otp_received = 1, otp_text = ? WHERE number = ?",
        (otp_text, number)
    )
    conn.commit()
    conn.close()

def get_unused_numbers():
    conn = sqlite3.connect("numbers.db")
    cursor = conn.cursor()
    cursor.execute("SELECT user_id, number, country, created_at FROM active_numbers WHERE otp_received = 0")
    rows = cursor.fetchall()
    conn.close()
    return rows

def get_user_last_number(user_id):
    conn = sqlite3.connect("numbers.db")
    cursor = conn.cursor()
    cursor.execute("SELECT number, country, otp_received FROM active_numbers WHERE user_id = ? ORDER BY id DESC LIMIT 1", (user_id,))
    row = cursor.fetchone()
    conn.close()
    return row

def get_number_owner_and_status(number):
    conn = sqlite3.connect("numbers.db")
    cursor = conn.cursor()
    cursor.execute("SELECT user_id, otp_received FROM active_numbers WHERE number = ?", (number,))
    row = cursor.fetchone()
    conn.close()
    return row

def add_premium_user(user_id):
    conn = sqlite3.connect("numbers.db")
    cursor = conn.cursor()
    cursor.execute("INSERT OR REPLACE INTO premium_users (user_id) VALUES (?)", (user_id,))
    conn.commit()
    conn.close()

def is_premium_user(user_id):
    if user_id == OWNER_ID:
        return True
    conn = sqlite3.connect("numbers.db")
    cursor = conn.cursor()
    cursor.execute("SELECT user_id FROM premium_users WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    return row is not None

# ==========================================
# LIVE STATS & API HELPER FUNCTIONS
# ==========================================
def fetch_live_country_stats():
    """Fetches real-time stock count per country from viewstats API."""
    stats = {}
    for url, token in [(API1_URL, API1_TOKEN), (API2_URL, API2_TOKEN)]:
        try:
            headers = {"Authorization": f"Bearer {token}"}
            res = requests.get(url, headers=headers, timeout=8)
            if res.status_code == 200:
                data = res.json()
                
                # Handling dictionary format: {"197": 70, "61": 15}
                if isinstance(data, dict):
                    items = data.get("stats", data.get("data", data))
                    if isinstance(items, dict):
                        for k, v in items.items():
                            if isinstance(v, (int, float)):
                                stats[str(k)] = stats.get(str(k), 0) + int(v)
                            elif isinstance(v, dict):
                                cnt = v.get("count", v.get("stock", v.get("total", 0)))
                                stats[str(k)] = stats.get(str(k), 0) + int(cnt)
                    elif isinstance(items, list):
                        for item in items:
                            c_code = str(item.get("country", item.get("code", item.get("country_id", ""))))
                            cnt = int(item.get("count", item.get("stock", item.get("total", 0))))
                            if c_code:
                                stats[c_code] = stats.get(c_code, 0) + cnt
                # Handling list format: [{"country": "197", "count": 70}]
                elif isinstance(data, list):
                    for item in data:
                        c_code = str(item.get("country", item.get("code", item.get("country_id", ""))))
                        cnt = int(item.get("count", item.get("stock", item.get("total", 0))))
                        if c_code:
                            stats[c_code] = stats.get(c_code, 0) + cnt
        except Exception as e:
            logging.error(f"Error fetching stats from {url}: {e}")

    return stats

def fetch_number_from_api(country_code="US"):
    headers1 = {"Authorization": f"Bearer {API1_TOKEN}"}
    headers2 = {"Authorization": f"Bearer {API2_TOKEN}"}
    params = {"country": country_code}

    for url, headers in [(API1_URL, headers1), (API2_URL, headers2)]:
        try:
            res = requests.get(url, headers=headers, params=params, timeout=10)
            if res.status_code == 200:
                data = res.json()
                if isinstance(data, dict) and "number" in data:
                    return str(data["number"])
                elif isinstance(data, list) and len(data) > 0 and "number" in data[0]:
                    return str(data[0]["number"])
        except Exception as e:
            logging.error(f"API Fetch Error ({url}): {e}")

    return None

def fetch_otp_from_api(phone_number):
    try:
        headers = {"x-api-key": API3_KEY}
        params = {"number": phone_number}
        res = requests.get(API3_URL, headers=headers, params=params, timeout=10)
        if res.status_code == 200:
            data = res.json()
            sms_list = data.get("reports", []) or data.get("sms", []) or (data if isinstance(data, list) else [])
            for sms in sms_list:
                msg = sms.get("message") or sms.get("sms_text") or str(sms)
                if msg:
                    return msg
    except Exception as e:
        logging.error(f"API3 Error: {e}")

    for url, token in [(API1_URL, API1_TOKEN), (API2_URL, API2_TOKEN)]:
        try:
            headers = {"Authorization": f"Bearer {token}"}
            params = {"number": phone_number}
            res = requests.get(url, headers=headers, params=params, timeout=10)
            if res.status_code == 200:
                data = res.json()
                sms_list = data.get("messages", []) or (data if isinstance(data, list) else [])
                for sms in sms_list:
                    msg = sms.get("message") or sms.get("text") or str(sms)
                    if msg:
                        return msg
        except Exception as e:
            logging.error(f"API OTP Error: {e}")

    return None

# ==========================================
# KEYBOARD MARKUPS
# ==========================================
def main_menu_keyboard():
    markup = types.InlineKeyboardMarkup(row_width=2)
    btn_get = types.InlineKeyboardButton("📱 Get Number Panel", callback_data="panel_get_number")
    btn_my_num = types.InlineKeyboardButton("📩 Check My OTP", callback_data="panel_check_otp")
    btn_help = types.InlineKeyboardButton("ℹ️ Help", callback_data="panel_help")
    markup.add(btn_get)
    markup.add(btn_my_num, btn_help)
    return markup

def country_selection_keyboard():
    markup = types.InlineKeyboardMarkup(row_width=2)
    buttons = []
    
    # Fetch live counts from API
    stats = fetch_live_country_stats()
    
    # Fallback default list if API stats empty
    if not stats:
        stats = {"IN": 50, "197": 70, "61": 15, "901": 90, "38": 38, "3": 3, "18": 18, "336": 336, "608": 608, "103": 103, "2": 2, "117": 117, "US": 100}

    for code, count in stats.items():
        if count <= 0:
            continue
            
        flag, name = COUNTRY_MAP.get(code, ("🌐", f"Country {code}"))
        
        # Special Label for India Premium
        if code == "IN":
            btn_label = f"{flag} {name} ⭐ [{count}]"
        else:
            btn_label = f"{flag} {name} [{count}]"
            
        buttons.append(types.InlineKeyboardButton(btn_label, callback_data=f"getnum_{code}"))

    # Adding buttons to markup
    markup.add(*buttons)
    markup.add(types.InlineKeyboardButton("🔙 Back to Main Menu", callback_data="main_menu"))
    return markup

# ==========================================
# BOT HANDLERS
# ==========================================
@bot.message_handler(commands=['start'])
def send_welcome(message):
    welcome_text = (
        f"👋 <b>Welcome back {message.from_user.first_name}!</b>\n\n"
        f"Aap yahan se virtual numbers aur unke OTP aasani se prapt kar sakte hain.\n"
        f"Neeche diye gaye panel se <b>Get Number Panel</b> par click karein."
    )
    bot.send_message(message.chat.id, welcome_text, reply_markup=main_menu_keyboard())

@bot.message_handler(commands=['premium'])
def add_premium_command(message):
    if message.from_user.id != OWNER_ID:
        bot.reply_to(message, "❌ <i>Yeh command sirf Bot Owner ke liye hai.</i>")
        return

    try:
        args = message.text.split()
        if len(args) < 2:
            bot.reply_to(message, "⚠️ <b>Usage:</b> <code>/premium <USER_ID></code>")
            return

        target_user_id = int(args[1])
        add_premium_user(target_user_id)
        bot.reply_to(message, f"✅ <b>User ID <code>{target_user_id}</code> is now a PREMIUM User!</b>")
        
        try:
            bot.send_message(target_user_id, "🎉 <b>Congratulations! Aapko Premium Access de diya gaya hai. Ab aap India (🇮🇳) ke numbers use kar sakte hain.</b>")
        except Exception:
            pass

    except ValueError:
        bot.reply_to(message, "❌ Invalid User ID. Numerical ID likhein.")
    except Exception as e:
        bot.reply_to(message, f"❌ Error: {e}")

@bot.message_handler(commands=['number'])
def owner_unused_numbers(message):
    if message.from_user.id != OWNER_ID:
        bot.reply_to(message, "❌ <i>Yeh command sirf Bot Owner ke liye hai.</i>")
        return

    unused = get_unused_numbers()
    if not unused:
        bot.reply_to(message, "✅ <b>Sabhi numbers par OTP aa chuka hai! Koi bhi unused number baki nahi hai.</b>")
        return

    report = f"📊 <b>Unused Numbers List ({len(unused)} Total):</b>\n\n"
    for idx, (user_id, number, country, created_at) in enumerate(unused, 1):
        report += f"<b>{idx}. Number:</b> <code>{number}</code>\n"
        report += f"   • Country: {country}\n"
        report += f"   • User ID: <code>{user_id}</code>\n"
        report += f"   • Created: {created_at}\n\n"

    if len(report) > 4000:
        for chunk in [report[i:i+4000] for i in range(0, len(report), 4000)]:
            bot.send_message(message.chat.id, chunk)
    else:
        bot.send_message(message.chat.id, report)

@bot.callback_query_handler(func=lambda call: True)
def callback_listener(call):
    chat_id = call.message.chat.id
    user_id = call.from_user.id

    try:
        if call.data == "main_menu":
            bot.edit_message_text(
                "<b>Welcome to Virtual OTP Service!</b> 👋\nChoose an option from below:",
                chat_id=chat_id,
                message_id=call.message.message_id,
                reply_markup=main_menu_keyboard()
            )

        elif call.data == "panel_get_number":
            bot.answer_callback_query(call.id, "Loading Live Country Stock...")
            bot.edit_message_text(
                "🌍 <b>Select Country for Virtual Number:</b>\n\nChoose the country where numbers are available:",
                chat_id=chat_id,
                message_id=call.message.message_id,
                reply_markup=country_selection_keyboard()
            )

        elif call.data.startswith("getnum_"):
            country_code = call.data.split("_")[1]
            
            # Premium Check for India
            if country_code == "IN" and not is_premium_user(user_id):
                premium_msg = (
                    "⭐ <b>India (🇮🇳) numbers are for PREMIUM users only!</b>\n\n"
                    "Premium lene ke liye contact kare:\n"
                    "👉 @FREE_FIRE_INDIA_GROUP"
                )
                markup = types.InlineKeyboardMarkup()
                markup.add(types.InlineKeyboardButton("💬 Contact for Premium", url="https://t.me/FREE_FIRE_INDIA_GROUP"))
                markup.add(types.InlineKeyboardButton("🔙 Select Other Country", callback_data="panel_get_number"))
                bot.send_message(chat_id, premium_msg, reply_markup=markup)
                return

            bot.answer_callback_query(call.id, "Fetching number from server...")
            number = fetch_number_from_api(country_code)
            
            if number:
                add_number_record(user_id, number, country_code)
                
                markup = types.InlineKeyboardMarkup()
                markup.add(types.InlineKeyboardButton("📩 Check OTP Now", callback_data=f"chk_{number}"))
                markup.add(types.InlineKeyboardButton("🔙 Back to Menu", callback_data="main_menu"))

                text = (
                    f"✅ <b>Number Generated Successfully!</b>\n\n"
                    f"📱 <b>Number:</b> <code>{number}</code>\n"
                    f"🏳️ <b>Country Code:</b> {country_code}\n\n"
                    f"<i>Yeh number aapke naam save ho gaya hai. OTP isi chat me aayega.</i>"
                )
                bot.send_message(chat_id, text, reply_markup=markup)
            else:
                markup = types.InlineKeyboardMarkup()
                markup.add(types.InlineKeyboardButton("🔄 Try Again", callback_data="panel_get_number"))
                bot.send_message(chat_id, "❌ <i>No numbers currently available for this country. Please try another country.</i>", reply_markup=markup)

        elif call.data.startswith("chk_"):
            number = call.data.split("_")[1]
            bot.answer_callback_query(call.id, "Checking OTP...")

            record = get_number_owner_and_status(number)
            if record:
                owner_id_db, otp_received_db = record
                
                if otp_received_db == 1:
                    bot.send_message(chat_id, f"⚠️ <i>Is number ke liye OTP pehle hi deliver kiya ja chuka hai.</i>")
                    return

                otp_msg = fetch_otp_from_api(number)
                if otp_msg:
                    mark_otp_received(number, otp_msg)
                    
                    digits = re.findall(r'\b\d{4,8}\b', otp_msg)
                    code_text = f"<code>{digits[0]}</code>" if digits else "See message below"

                    response = (
                        f"🎉 <b>OTP Received!</b>\n\n"
                        f"📱 <b>Number:</b> <code>{number}</code>\n"
                        f"🔑 <b>Code:</b> {code_text}\n\n"
                        f"📩 <b>Full Message:</b>\n<code>{otp_msg}</code>"
                    )
                    bot.send_message(owner_id_db, response)
                else:
                    markup = types.InlineKeyboardMarkup()
                    markup.add(types.InlineKeyboardButton("🔄 Check Again", callback_data=f"chk_{number}"))
                    markup.add(types.InlineKeyboardButton("🔙 Main Menu", callback_data="main_menu"))
                    bot.send_message(chat_id, f"⏳ <b>OTP Pending for</b> <code>{number}</code>\n\nPlease wait 10-20 seconds and click Check Again.", reply_markup=markup)
            else:
                bot.send_message(chat_id, "❌ <i>Number record not found.</i>")

        elif call.data == "panel_check_otp":
            last_record = get_user_last_number(user_id)
            if last_record:
                number, country, otp_status = last_record
                markup = types.InlineKeyboardMarkup()
                markup.add(types.InlineKeyboardButton("📩 Check OTP", callback_data=f"chk_{number}"))
                markup.add(types.InlineKeyboardButton("🔙 Main Menu", callback_data="main_menu"))
                
                status_text = "✅ OTP Received" if otp_status == 1 else "⏳ Waiting for OTP"
                bot.send_message(
                    chat_id,
                    f"📱 Your last active number: <code>{number}</code> ({country})\nStatus: {status_text}",
                    reply_markup=markup
                )
            else:
                bot.answer_callback_query(call.id, "Aapne abhi tak koi number request nahi kiya!", show_alert=True)

        elif call.data == "panel_help":
            help_text = (
                "<b>ℹ️ How to use this Bot:</b>\n\n"
                "1. Click on <b>Get Number Panel</b>.\n"
                "2. Choose your preferred country.\n"
                "3. Copy the generated number and paste it in your app.\n"
                "4. Click <b>Check OTP</b>. OTP direct aapke DM me bhej diya jayega."
            )
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton("🔙 Back", callback_data="main_menu"))
            bot.send_message(chat_id, help_text, reply_markup=markup)

    except Exception as e:
        logging.error(f"Error handling callback: {e}")

# ==========================================
# MAIN EXECUTION THREADS
# ==========================================
if __name__ == "__main__":
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.daemon = True
    flask_thread.start()

    ping_thread = threading.Thread(target=keep_alive_ping)
    ping_thread.daemon = True
    ping_thread.start()

    print("Bot is running with live country stock stats...")
    bot.infinity_polling(skip_pending=True) 
