
import os
import sqlite3
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    MessageHandler, ContextTypes, filters, ConversationHandler
)

TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))

DB = "shop.db"
PRODUCTS = [
    {"id": "p1", "name": "Marshmallow အခြောက်", "price": 3000},
    {"id": "p2", "name": "ကကျွတ်ကကျွတ်ဝါး", "price": 2000},
]

PRODUCT, QUANTITY, NAME, PHONE, ADDRESS = range(5)


def init_db():
    with sqlite3.connect(DB) as con:
        con.execute("""
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                product TEXT, quantity INTEGER, total INTEGER,
                customer TEXT, phone TEXT, address TEXT
            )
        """)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton(
            f"{p['name']} - {p['price']} ကျပ်",
            callback_data=p["id"]
        )]
        for p in PRODUCTS
    ]
    await update.message.reply_text(
        "မင်္ဂလာပါရှင့်။ ကျွန်မတို့ဆိုင်မှ ကြိုဆိုပါတယ်။ 🛍️\n"
        "ဝယ်ယူလိုသောပစ္စည်းကို ရွေးချယ်ပေးပါ။",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return PRODUCT


async def choose_product(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    product = next(
        (p for p in PRODUCTS if p["id"] == query.data), None
    )
    if not product:
        await query.message.reply_text("ပစ္စည်းမတွေ့ပါ။ /start ပြန်နှိပ်ပါ။")
        return ConversationHandler.END

    context.user_data["product"] = product
    await query.message.reply_text(
        f"ရွေးထားသောပစ္စည်း - {product['name']}\n"
        "ဘယ်နှစ်ခု ဝယ်ယူချင်ပါသလဲ။"
    )
    return QUANTITY


async def quantity(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        qty = int(update.message.text)
        if qty < 1 or qty > 1000:
            raise ValueError
    except ValueError:
        await update.message.reply_text("အရေအတွက်ကို 1 မှ 1000 အတွင်း ဂဏန်းနဲ့ရေးပေးပါ။")
        return QUANTITY

    context.user_data["quantity"] = qty
    await update.message.reply_text("ဝယ်ယူသူအမည် ရေးပေးပါ။")
    return NAME


async def customer_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["name"] = update.message.text
    await update.message.reply_text("ဖုန်းနံပါတ် ရေးပေးပါ။")
    return PHONE


async def phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["phone"] = update.message.text
    await update.message.reply_text("ပစ္စည်းပို့ရမယ့် လိပ်စာ ရေးပေးပါ။")
    return ADDRESS


async def address(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["address"] = update.message.text

    p = context.user_data["product"]
    qty = context.user_data["quantity"]
    total = p["price"] * qty

    with sqlite3.connect(DB) as con:
        cur = con.execute(
            """INSERT INTO orders
            (product, quantity, total, customer, phone, address)
            VALUES (?, ?, ?, ?, ?, ?)""",
            (p["name"], qty, total,
             context.user_data["name"],
             context.user_data["phone"],
             context.user_data["address"])
        )
        order_id = cur.lastrowid

    summary = (
        f"🛍️ အော်ဒါအတည်ပြုရန်\n"
        f"အော်ဒါနံပါတ် - #{order_id}\n"
        f"ပစ္စည်း - {p['name']}\n"
        f"အရေအတွက် - {qty}\n"
        f"စုစုပေါင်း - {total:,} ကျပ်\n"
        f"အမည် - {context.user_data['name']}\n"
        f"ဖုန်း - {context.user_data['phone']}\n"
        f"လိပ်စာ - {context.user_data['address']}"
    )

    await update.message.reply_text(
        summary + "\n\nကျေးဇူးတင်ပါတယ်။ ဆိုင်မှ ဆက်သွယ်ပေးပါမယ်။"
    )

    if ADMIN_ID:
        try:
            await context.bot.send_message(ADMIN_ID, "📦 အော်ဒါအသစ်\n\n" + summary)
        except Exception:
            pass

    context.user_data.clear()
    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text("အော်ဒါပယ်ဖျက်လိုက်ပါပြီ။ /start နဲ့ ပြန်စနိုင်ပါတယ်။")
    return ConversationHandler.END


async def myid(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"သင့် Telegram ID: {update.effective_user.id}")


def main():
    if not TOKEN:
        raise RuntimeError("BOT_TOKEN မထည့်ရသေးပါ။")

    init_db()
    app = Application.builder().token(TOKEN).build()

    conv = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            PRODUCT: [CallbackQueryHandler(choose_product)],
            QUANTITY: [MessageHandler(filters.TEXT & ~filters.COMMAND, quantity)],
            NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, customer_name)],
            PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, phone)],
            ADDRESS: [MessageHandler(filters.TEXT & ~filters.COMMAND, address)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    app.add_handler(CommandHandler("myid", myid))
    app.add_handler(conv)
    print("Telegram Shop Bot is running...")
    app.run_polling()


if __name__ == "__main__":
    main()
