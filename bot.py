import telebot
from telebot import types

# သင့် Token
BOT_TOKEN = '9137505282:AAGBgzFqOi4Z42IJSDt9WZzTSAUsmgO-3bA'

# သင့် Telegram User ID
OWNER_ID = '8737881994'

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
    bot.reply_to(message, f"စုစုပေါင်း {user_orders[uid]['total']} ကျပ် ဖြစ်ပါတယ်။\nကျေးဇူးပြုပြီး သင့်ရဲ့ **အမည်** ကို ရိုက်ထည့်ပါ။")
    bot.register_next_step_handler(message, process_name) # အမည် မေးတဲ့အဆင့်ကို ပြောင်းလိုက်တယ်

# အမည် လက်ခံပြီး ဖုန်းနံပါတ် ဆက်မေးမယ်
def process_name(message):
    uid = message.from_user.id
    if uid in user_orders:
        user_orders[uid]['name'] = message.text
        bot.reply_to(message, "ကျေးဇူးတင်ပါတယ်။\nကျေးဇူးပြုပြီး သင့်ရဲ့ **ဖုန်းနံပါတ်** ကို ရိုက်ထည့်ပါ။")
        bot.register_next_step_handler(message, process_phone)
    else:
        bot.reply_to(message, "တစ်ခုခု မှားယွင်းသွားပါတယ်။ /start ကနေ ပြန်စပါ။")

# ဖုန်းနံပါတ် လက်ခံပြီး လိပ်စာ ဆက်မေးမယ်
def process_phone(message):
    uid = message.from_user.id
    if uid in user_orders:
        user_orders[uid]['phone'] = message.text
        bot.reply_to(message, "ကျေးဇူးတင်ပါတယ်။\nနောက်ဆုံးအနေနဲ့ ပို့ဆောင်ရမယ့် **မြို့နဲ့ ရပ်ကွက်/လိပ်စာအပြည့်အစုံ** ကို ရိုက်ထည့်ပေးပါ။")
        bot.register_next_step_handler(message, process_address)
    else:
        bot.reply_to(message, "တစ်ခုခု မှားယွင်းသွားပါတယ်။ /start ကနေ ပြန်စပါ။")

# လိပ်စာ လက်ခံပြီး Order အပြည့်အစုံကို ဆိုင်ပိုင်ရှင်ဆီ ပို့မယ်
def process_address(message):
    uid = message.from_user.id
    o = user_orders.get(uid)
    if not o:
        bot.reply_to(message, "တစ်ခုခု မှားယွင်းသွားပါတယ်။ /start ကနေ ပြန်စပါ။")
        return
    
    o['address'] = message.text
    
    # ဆိုင်ပိုင်ရှင်ဆီ ပို့မယ့် စာ
    summary = (f"✅ Order အသစ်\n"
               f"--------------------\n"
               f"ပစ္စည်း: {o['product']}\n"
               f"အရေအတွက်: {o['quantity']} ဘူး\n"
               f"စုစုပေါင်း: {o['total']} ကျပ်\n"
               f"--------------------\n"
               f"အမည်: {o['name']}\n"
               f"ဖုန်း: {o['phone']}\n"
               f"လိပ်စာ: {o['address']}\n"
               f"--------------------\n"
               f"Telegram Acc Name: {message.from_user.first_name}\n"
               f"User ID: {uid}")
    
    # ဝယ်သူကို စာပြန်မယ်
    bot.reply_to(message, "ကျေးဇူးတင်ပါတယ်! သင့် order နဲ့ လိပ်စာကို လက်ခံရရှိပါပြီ။ မကြာမီ ဆက်သွယ်ပါမယ်။")
    
    # ဆိုင်ပိုင်ရှင် (သင့်) ဆီကို Order ပို့မယ်
    try:
        bot.send_message(OWNER_ID, summary)
    except Exception as e:
        print(f"Owner ဆီ စာပို့လို့မရပါ: {e}")
        
    del user_orders[uid]

print("Bot running...")
bot.infinity_polling()
