import requests
import telebot
from telebot import types

# --- CONFIGURATION ---
BOT_TOKEN = "8975309935:AAHxkl1KYhkYovlwun1CrXFz7la9dvaRx1o"
ADMIN_ID = 8916566500
SHEETDB_URL = "https://sheetdb.io/api/v1/aa3kz7frbq81x"

bot = telebot.TeleBot(BOT_TOKEN)
user_data = {}

@bot.message_handler(commands=['start'])
def start_command(message):
    chat_id = message.chat.id
    user_data[chat_id] = {}
    
    msg = bot.send_message(
        chat_id,
        "👋 **Welcome to our Official Channel Bot!**\n\nPlease enter your **Full Name** below:",
        parse_mode="Markdown"
    )
    bot.register_next_step_handler(msg, process_name)

def process_name(message):
    chat_id = message.chat.id
    user_data[chat_id]["name"] = message.text

    markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    btn = types.KeyboardButton(text="📱 Share Phone Number", request_contact=True)
    markup.add(btn)

    msg = bot.send_message(
        chat_id, 
        "Thanks! Now please share your phone number using the button below:", 
        reply_markup=markup
    )
    bot.register_next_step_handler(msg, process_phone)

def process_phone(message):
    chat_id = message.chat.id
    if message.contact:
        phone = message.contact.phone_number
    else:
        phone = message.text

    user_data[chat_id]["phone"] = phone

    markup = types.ReplyKeyboardRemove()
    msg = bot.send_message(
        chat_id, 
        "Great! Now please tell me what you are looking for (Notes, Software, Deals, etc.):", 
        reply_markup=markup
    )
    bot.register_next_step_handler(msg, process_request)

def process_request(message):
    chat_id = message.chat.id
    user_data[chat_id]["request"] = message.text

    # SheetDB Data Saving
    data = {
        "data": {
            "Name": user_data[chat_id]["name"],
            "Phone": user_data[chat_id]["phone"],
            "Request": user_data[chat_id]["request"],
            "TelegramID": str(chat_id)
        }
    }
    
    try:
        requests.post(SHEETDB_URL, json=data)
    except Exception as e:
        print("SheetDB Error:", e)

    # User Confirmation Message
    bot.send_message(
        chat_id,
        "✅ **Thank you!** Your request has been saved successfully. We will reach out to you soon."
    )

    # Admin Notification
    admin_text = (
        f"🚨 **New Lead Received!**\n\n"
        f"👤 **Name:** {user_data[chat_id]['name']}\n"
        f"📞 **Phone:** {user_data[chat_id]['phone']}\n"
        f"💬 **Request:** {user_data[chat_id]['request']}\n"
        f"🆔 **Telegram ID:** {chat_id}"
    )
    try:
        bot.send_message(ADMIN_ID, admin_text, parse_mode="Markdown")
    except Exception as e:
        print("Admin Notification Error:", e)

# Admin Broadcast Command (/send)
@bot.message_handler(commands=['send'])
def send_broadcast(message):
    if message.chat.id != ADMIN_ID:
        bot.send_message(message.chat.id, "You are not authorized.")
        return

    text_to_send = message.text.replace("/send", "").strip()
    if not text_to_send:
        bot.send_message(message.chat.id, "Please provide the message text after /send.")
        return

    try:
        response = requests.get(SHEETDB_URL)
        users = response.json()
        success_count = 0
        for user in users:
            t_id = user.get("TelegramID")
            if t_id:
                try:
                    bot.send_message(t_id, text_to_send)
                    success_count += 1
                except Exception:
                    pass
        bot.send_message(ADMIN_ID, f"✅ Broadcast sent successfully to {success_count} users!")
    except Exception as e:
        bot.send_message(ADMIN_ID, f"❌ Failed: {e}")

if __name__ == "__main__":
    print("Bot is running...")
    bot.infinity_polling()
