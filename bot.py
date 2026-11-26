import telebot
from telebot import types

# သင့် Bot Token ကို ဒီမှာ ထည့်ပါ (မျဉ်းစောင်းတွေကို မဖျက်ပါနဲ့)
BOT_TOKEN = '9270576168:AAECsHFTq0scRzY2cgLpmrVac0eWMwksvDA'
bot = telebot.TeleBot(BOT_TOKEN)

# ဆိုင်က ပစ္စည်းတွေ
PRODUCTS = {
    "1": {"name": "ကကျွတ်ကကျွတ်ဝါး (၁) ဘူး", "price": 30000},
    "2": {"name": "Marshmallow (၁) ဘူး", "price": 25000}
}

user_orders = {}

@bot.message_handler(commands=['start'])
def send_welcome(message):
    markup = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
    markup.add(types.KeyboardButton("🛍️ ပစ္စည်းမီနူး ကြည့်မယ်"))
    bot.send_message(message.chat.id, "မင်္ဂလာပါ! ဆိုင်မှ ကြိုဆိုပါတယ်။", reply_markup=markup)

@bot.message_handler(func=lambda m: m.text == "🛍️ ပစ္စည်းမီနူး ကြည့်မယ်")
def show_menu(message):
    markup = types.InlineKeyboardMarkup(row_width=1)
    for key, p in PRODUCTS.items():
        markup.add(types.InlineKeyboardButton(f"{p['name']} - {p['price']} ကျပ်", callback_data=f"select_{key}"))
    bot.send_message(message.chat.id, "အောက်က ပစ္စည်းတွေထဲက ရွေးပါ:", reply_markup=markup)

@bot.callback_query_handler(func=lambda c: c.data.startswith('select_'))
def handle_selection(call):
    key = call.data.split('_')[1]
    p = PRODUCTS[key]
    user_orders[call.from_user.id] = {"product": p['name'], "price": p['price']}
    bot.answer_callback_query(call.id)
    bot.send_message(call.message.chat.id, f"သင် '{p['name']}' ကို ရွေးထားပါတယ်။\nဘယ်နှစ်ဘူး ယူမလဲ? (ဂဏန်းပဲ ရိုက်ထည့်ပါ)")
    bot.register_next_step_handler(call.message, process_qty)

def process_qty(message):
    try:
        qty = int(message.text)
        if qty <= 0: raise ValueError
    except ValueError:
        bot.reply_to(message, "ဂဏန်းမှန်မှန် ရိုက်ထည့်ပါ (ဥပမာ - 1, 2, 3)")
        bot.register_next_step_handler(message, process_qty)
        return
    uid = message.from_user.id
    user_orders[uid]['quantity'] = qty
    user_orders[uid]['total'] = user_orders[uid]['price'] * qty
    bot.reply_to(message, f"စုစုပေါင်း {user_orders[uid]['total']} ကျပ် ဖြစ်ပါတယ်။\nကျေးဇူးပြုပြီး သင့်ရဲ့ ဖုန်းနံပါတ် ကို ရိုက်ထည့်ပါ။")
    bot.register_next_step_handler(message, process_phone)

def process_phone(message):
    uid = message.from_user.id
    o = user_orders.get(uid)
    if not o:
        bot.reply_to(message, "တစ်ခုခု မှားယွင်းသွားပါတယ်။ /start ကနေ ပြန်စပါ။")
        return
    summary = (f"✅ Order အသစ်\n"
               f"ပစ္စည်း: {o['product']}\n"
               f"အရေအတွက်: {o['quantity']} ဘူး\n"
               f"စုစုပေါင်း: {o['total']} ကျပ်\n"
               f"ဖုန်း: {message.text}\n"
               f"User ID: {uid}")
    bot.reply_to(message, "ကျေးဇူးတင်ပါတယ်! သင့် order ကို လက်ခံရရှိပါပြီ။ မကြာမီ ဆက်သွယ်ပါမယ်။")
    bot.send_message(message.chat.id, summary)
    del user_orders[uid]

print("Bot running...")
bot.infinity_polling()
