import logging
import os
from threading import Thread
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)

# --- Web Server (Render အတွက် လိုအပ်ချက်) ---
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is alive!"

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)

# --- Bot Code ---
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

# ==========================================
# သင့် Bot Token အသစ် နဲ့ Admin ID
# ==========================================
BOT_TOKEN = "9145591850:AAE9F3hKuLO606aqJnOPzTmiADG4W_J6TTQ"
ADMIN_ID = "9242816269" 

# ==========================================
# သင့်ရဲ့ ပစ္စည်းစာရင်း (Menu)
# ==========================================
PRODUCTS = {
    "item_1": "ကကျွတ်ကကျွတ်ဝါးငါးခြောက်ကြော် - ၁ ဘူး (၃၀,၀၀၀ ကျပ်)",
    "item_2": "မတ်မယ်လိုအခြောက် - ၁ ထုပ် (၂၀,၀၀၀ ကျပ်)",
}

user_states = {}
STATE_WAITING_FOR_PRODUCT = "waiting_for_product"
STATE_WAITING_FOR_QUANTITY = "waiting_for_quantity"
STATE_WAITING_FOR_ADDRESS = "waiting_for_address"
STATE_WAITING_FOR_PHONE = "waiting_for_phone"


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    user_states[user_id] = {"state": STATE_WAITING_FOR_PRODUCT, "data": {}}
    await send_rich_menu(update, context)


async def send_rich_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    rich_text = "<b>ဘာများ လိုအပ်ပါလဲခင်ဗျာ?</b>\n\n"
    rich_text += "အောက်ပါ Menu ထဲကနေ သင်ဝယ်ယူလိုတဲ့ ပစ္စည်းကို ရွေးချယ်ပေးပါ -\n\n"

    for key, name in PRODUCTS.items():
        rich_text += f"• {name}\n"

    keyboard = []
    for key, name in PRODUCTS.items():
        keyboard.append([InlineKeyboardButton(name, callback_data=f"select_{key}")])

    reply_markup = InlineKeyboardMarkup(keyboard)

    if update.message:
        await update.message.reply_text(rich_text, reply_markup=reply_markup, parse_mode="HTML")
    elif update.callback_query:
        await update.callback_query.edit_message_text(rich_text, reply_markup=reply_markup, parse_mode="HTML")


async def handle_product_selection(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    data = query.data

    selected_key = data.replace("select_", "")
    selected_product_name = PRODUCTS.get(selected_key, "Unknown")

    user_states[user_id] = {
        "state": STATE_WAITING_FOR_QUANTITY,
        "data": {"product": selected_product_name, "product_key": selected_key},
    }

    await query.edit_message_text(
        text=f"သင်ရွေးချယ်လိုက်တာက - <b>{selected_product_name}</b>\n\n"
        f"ဘယ်လောက် ဝယ်ယူလိုပါသလဲခင်ဗျာ? (အရေအတွက် ဂဏန်းကို ရိုက်ထည့်ပေးပါ)",
        parse_mode="HTML",
    )


async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    text = update.message.text.strip()

    if user_id not in user_states:
        await update.message.reply_text("ကျေးဇူးပြုပြီး စတင်ရန် /start ကို နှိပ်ပေးပါ။")
        return

    current_state = user_states[user_id]["state"]

    if current_state == STATE_WAITING_FOR_QUANTITY:
        if not text.isdigit():
            await update.message.reply_text("ကျေးဇူးပြုပြီး အရေအတွက်ကို ဂဏန်းနဲ့ပဲ ရိုက်ထည့်ပေးပါခင်ဗျာ။")
            return
        
        user_states[user_id]["data"]["quantity"] = text
        user_states[user_id]["state"] = STATE_WAITING_FOR_ADDRESS
        
        await update.message.reply_text(
            f"အရေအတွက် - <b>{text}</b> လို့ မှတ်သားလိုက်ပါပြီ။\n\n"
            f"ကျေးဇူးပြုပြီး သင့်ရဲ့ <b>နေရပ်လိပ်စာ</b> (ပို့ဆောင်ရမယ့် လိပ်စာအပြည့်အစုံ) ကို ရိုက်ထည့်ပေးပါ။",
            parse_mode="HTML",
        )

    elif current_state == STATE_WAITING_FOR_ADDRESS:
        user_states[user_id]["data"]["address"] = text
        user_states[user_id]["state"] = STATE_WAITING_FOR_PHONE
        
        await update.message.reply_text(
            f"လိပ်စာကို မှတ်သားလိုက်ပါပြီ။\n\n"
            f"နောက်ဆုံးအနေနဲ့ သင့်ရဲ့ <b>ဖုန်းနံပါတ်</b> ကို ရိုက်ထည့်ပေးပါ။",
            parse_mode="HTML",
        )

    elif current_state == STATE_WAITING_FOR_PHONE:
        user_states[user_id]["data"]["phone"] = text
        
        data = user_states[user_id]["data"]
        summary = (
            f"<b>အတည်ပြုချက်</b>\n\n"
            f"ပစ္စည်း: {data.get('product')}\n"
            f"အရေအတွက်: {data.get('quantity')}\n"
            f"နေရပ်လိပ်စာ: {data.get('address')}\n"
            f"ဖုန်းနံပါတ်: {data.get('phone')}\n\n"
            f"သင့်ရဲ့ အချက်အလက်တွေကို လက်ခံရရှိပါပြီ။ မကြာမီ ဆက်သွယ်ပေးပါမယ်။"
        )

        # ၁။ Customer ဆီကို အတည်ပြုစာ ပို့ခြင်း
        await update.message.reply_text(summary, parse_mode="HTML")

        # ၂။ ဆိုင်ရှင် (Admin) ဆီကို အသိပေးစာ ပို့ခြင်း
        admin_message = (
            f"🔔 <b>Order အသစ် ရောက်ပါပြီ!</b>\n\n"
            f"Customer: @{update.effective_user.username if update.effective_user.username else 'Username မရှိပါ'}\n"
            f"ပစ္စည်း: {data.get('product')}\n"
            f"အရေအတွက်: {data.get('quantity')}\n"
            f"နေရပ်လိပ်စာ: {data.get('address')}\n"
            f"ဖုန်းနံပါတ်: {data.get('phone')}"
        )
        
        try:
            await context.bot.send_message(chat_id=ADMIN_ID, text=admin_message, parse_mode="HTML")
        except Exception as e:
            print(f"Admin ဆီကို စာပို့လို့မရပါ: {e}")

        user_states.pop(user_id, None)


def main() -> None:
    # Flask ကို Background မှာ Run မယ်
    threading = Thread(target=run_flask)
    threading.start()
    
    application = Application.builder().token(BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(handle_product_selection, pattern="^select_"))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    print("Bot အလုပ်လုပ်နေပါပြီ...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
