import os
import random
import sqlite3
from datetime import date, timedelta

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputFile
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

# =========================================================
# TOKEN
# =========================================================
# Token endi environment variable (muhit o'zgaruvchisi) orqali olinadi.
# Localda ishlatish uchun terminalga quyidagini yozing (bir martalik):
#   Windows (cmd):      set BOT_TOKEN=tokeningiz
#   Windows (PowerShell): $env:BOT_TOKEN="tokeningiz"
#   Linux/Mac:           export BOT_TOKEN=tokeningiz
# Railway'da esa "Variables" bo'limiga BOT_TOKEN nomi bilan kiritasiz.

TOKEN = os.environ.get("BOT_TOKEN")

if not TOKEN:
    raise RuntimeError(
        "BOT_TOKEN topilmadi! Avval environment variable sifatida tokenni kiriting."
    )

# =========================================================
# 2000 TA SO'ZLIK BAZA
# Hozir namuna. Keyin shu ro'yxatni 2000 taga kengaytiramiz.
# =========================================================

WORDS = [
    ("делать", "qilmoq"),
    ("говорить", "gapirmoq"),
    ("сказать", "aytmoq"),
    ("спрашивать", "so‘ramoq"),
    ("отвечать", "javob bermoq"),
    ("понимать", "tushunmoq"),
    ("объяснять", "tushuntirmoq"),
    ("знать", "bilmoq"),
    ("думать", "o‘ylamoq"),
    ("хотеть", "xohlamoq"),
    ("мочь", "qila olmoq"),
    ("идти", "piyoda bormoq"),
    ("ехать", "transportda bormoq"),
    ("приходить", "kelmoq"),
    ("уходить", "ketmoq"),
    ("ждать", "kutmoq"),
    ("искать", "qidirmoq"),
    ("найти", "topmoq"),
    ("брать", "olmoq"),
    ("дать", "bermoq"),

    ("работать", "ishlamoq"),
    ("учиться", "o‘qimoq"),
    ("жить", "yashamoq"),
    ("любить", "sevmoq"),
    ("нравиться", "yoqmoq"),
    ("есть", "yemoq"),
    ("пить", "ichmoq"),
    ("спать", "uxlamoq"),
    ("проснуться", "uyg‘onmoq"),
    ("купить", "sotib olmoq"),
    ("продать", "sotmoq"),
    ("получить", "olmoq"),
    ("открыть", "ochmoq"),
    ("закрыть", "yopmoq"),
    ("начать", "boshlamoq"),
    ("закончить", "tugatmoq"),
    ("помочь", "yordam bermoq"),
    ("звонить", "qo‘ng‘iroq qilmoq"),
    ("писать", "yozmoq"),
    ("читать", "o‘qimoq"),

    ("сейчас", "hozir"),
    ("потом", "keyin"),
    ("сегодня", "bugun"),
    ("вчера", "kecha"),
    ("завтра", "ertaga"),
    ("уже", "allaqachon"),
    ("ещё", "hali / yana"),
    ("только", "faqat"),
    ("просто", "shunchaki"),
    ("часто", "tez-tez"),
    ("иногда", "ba’zan"),
    ("всегда", "har doim"),
    ("никогда", "hech qachon"),
    ("почему", "nima uchun"),
    ("поэтому", "shuning uchun"),
    ("потому что", "chunki"),
    ("если", "agar"),
    ("когда", "qachon"),
    ("конечно", "albatta"),
    ("наверное", "ehtimol"),

    ("работа", "ish"),
    ("начальник", "boshliq"),
    ("коллега", "hamkasb"),
    ("зарплата", "maosh"),
    ("деньги", "pul"),
    ("смена", "smena"),
    ("выходной", "dam olish kuni"),
    ("перерыв", "tanaffus"),
    ("магазин", "do‘kon"),
    ("цена", "narx"),
    ("скидка", "chegirma"),
    ("товар", "tovar"),
    ("день", "kun"),
    ("время", "vaqt"),
    ("город", "shahar"),
    ("улица", "ko‘cha"),
    ("дом", "uy"),
    ("комната", "xona"),
    ("машина", "mashina"),
    ("дорога", "yo‘l"),

    ("хороший", "yaxshi"),
    ("плохой", "yomon"),
    ("большой", "katta"),
    ("маленький", "kichik"),
    ("новый", "yangi"),
    ("старый", "eski"),
    ("дорогой", "qimmat"),
    ("дешёвый", "arzon"),
    ("быстрый", "tez"),
    ("медленный", "sekin"),
    ("важный", "muhim"),
    ("нужный", "kerakli"),
    ("свободный", "bo‘sh"),
    ("занятый", "band"),
    ("готовый", "tayyor"),
    ("трудный", "qiyin"),
    ("лёгкий", "oson"),
    ("интересный", "qiziqarli"),
    ("скучный", "zerikarli"),
    ("удобный", "qulay"),
]

# =========================================================
# DATABASE
# =========================================================

db = sqlite3.connect("russian_bot.db", check_same_thread=False)
cur = db.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    level INTEGER DEFAULT 1,
    xp INTEGER DEFAULT 0,
    stage INTEGER DEFAULT 1,
    streak INTEGER DEFAULT 0,
    last_day TEXT DEFAULT ''
)
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS mistakes (
    user_id INTEGER,
    word TEXT,
    translation TEXT,
    count INTEGER DEFAULT 1
)
""")

db.commit()


# =========================================================
# USER
# =========================================================

def get_user(user_id):
    cur.execute(
        "SELECT * FROM users WHERE user_id=?",
        (user_id,)
    )
    user = cur.fetchone()

    if not user:
        cur.execute(
            "INSERT INTO users(user_id) VALUES(?)",
            (user_id,)
        )
        db.commit()

        cur.execute(
            "SELECT * FROM users WHERE user_id=?",
            (user_id,)
        )
        user = cur.fetchone()

    return user


def add_xp(user_id, amount):
    get_user(user_id)

    cur.execute(
        "UPDATE users SET xp=xp+? WHERE user_id=?",
        (amount, user_id)
    )

    db.commit()

    update_level(user_id)


def update_level(user_id):
    cur.execute(
        "SELECT xp FROM users WHERE user_id=?",
        (user_id,)
    )
    xp = cur.fetchone()[0]

    level = max(1, xp // 1000 + 1)

    cur.execute(
        "UPDATE users SET level=? WHERE user_id=?",
        (level, user_id)
    )

    db.commit()


# =========================================================
# STREAK
# =========================================================

def update_streak(user_id):
    user = get_user(user_id)

    last_day = user[5]
    today = date.today()

    if last_day == str(today):
        return

    if last_day:
        yesterday = today - timedelta(days=1)

        if last_day == str(yesterday):
            cur.execute(
                "UPDATE users SET streak=streak+1,last_day=? WHERE user_id=?",
                (str(today), user_id)
            )
        else:
            cur.execute(
                "UPDATE users SET streak=1,last_day=? WHERE user_id=?",
                (str(today), user_id)
            )
    else:
        cur.execute(
            "UPDATE users SET streak=1,last_day=? WHERE user_id=?",
            (str(today), user_id)
        )

    db.commit()


# =========================================================
# MENU
# =========================================================

def main_menu():
    keyboard = [
        [
            InlineKeyboardButton("📚 Bugungi so‘zlar", callback_data="today"),
            InlineKeyboardButton("🎮 O‘yinlar", callback_data="games"),
        ],
        [
            InlineKeyboardButton("📝 Imtihon", callback_data="exam"),
            InlineKeyboardButton("❌ Xatolarim", callback_data="mistakes"),
        ],
        [
            InlineKeyboardButton("📊 Statistika", callback_data="stats"),
            InlineKeyboardButton("🏆 Reyting", callback_data="rank"),
        ],
    ]

    return InlineKeyboardMarkup(keyboard)


# =========================================================
# START
# =========================================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_id = update.effective_user.id

    get_user(user_id)
    update_streak(user_id)

    text = (
        "🇷🇺 RUS TILI TRAINER\n\n"
        "Salom! 👋\n"
        "Rus tilini o‘yin orqali o‘rganamiz.\n\n"
        "📚 20 ta yangi so‘z\n"
        "🎮 Qiziqarli o‘yinlar\n"
        "🔊 Talaffuz\n"
        "📝 Imtihon\n"
        "⭐ XP va Level\n"
        "🔥 Streak\n\n"
        "Boshlash uchun tugmalardan foydalan."
    )

    # banner.jpg bo'lsa rasm yuboradi
    if os.path.exists("banner.jpg"):
        with open("banner.jpg", "rb") as banner_file:
            await update.message.reply_photo(
                photo=InputFile(banner_file),
                caption=text,
                reply_markup=main_menu()
            )
    else:
        await update.message.reply_text(
            text,
            reply_markup=main_menu()
        )


# =========================================================
# TODAY
# =========================================================

async def today(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_id = update.effective_user.id
    user = get_user(user_id)

    stage = user[3]

    start_index = (stage - 1) * 20
    words = WORDS[start_index:start_index + 20]

    if len(words) < 20:
        await update.message.reply_text(
            "🎉 Barcha mavjud so‘zlarni tugatding!"
        )
        return

    text = f"📚 {stage}-BOSQICH\n\n"

    for i, (ru, uz) in enumerate(words, 1):
        text += f"{i}. 🇷🇺 {ru} — 🇺🇿 {uz}\n"

    text += (
        "\n🧠 Shu 20 ta so‘zni o‘rgan.\n"
        "Keyin 📝 Imtihonni topshir."
    )

    await update.message.reply_text(
        text,
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🎮 O‘yin boshlash", callback_data="games")],
            [InlineKeyboardButton("📝 Imtihon", callback_data="exam")]
        ])
    )


# =========================================================
# GAMES MENU
# =========================================================

async def games(update: Update, context: ContextTypes.DEFAULT_TYPE):

    keyboard = [
        [InlineKeyboardButton("🇺🇿 To‘g‘ri tarjimani top", callback_data="game_translate")],
        [InlineKeyboardButton("🇷🇺 Ruschasini top", callback_data="game_russian")],
        [InlineKeyboardButton("🔊 Talaffuz", callback_data="game_pronounce")],
        [InlineKeyboardButton("⚡ Tezkor test", callback_data="game_fast")],
    ]

    await update.callback_query.edit_message_text(
        "🎮 O‘YINLAR\n\nQaysi o‘yinni o‘ynaymiz?",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# =========================================================
# TRANSLATION GAME
# =========================================================

async def translation_game(query):

    word = random.choice(WORDS)

    ru, correct = word

    options = [correct]

    while len(options) < 3:
        fake = random.choice(WORDS)[1]

        if fake not in options:
            options.append(fake)

    random.shuffle(options)

    keyboard = []

    for option in options:
        keyboard.append([
            InlineKeyboardButton(
                option,
                callback_data=f"answer|{ru}|{correct}|{option}"
            )
        ])

    await query.edit_message_text(
        f"🇷🇺 **{ru}**\n\n"
        "Qaysi tarjimasi to‘g‘ri?",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# =========================================================
# EXAM
# =========================================================

async def exam(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    user_id = query.from_user.id

    user = get_user(user_id)
    stage = user[3]

    start_index = (stage - 1) * 20
    words = WORDS[start_index:start_index + 20]

    if len(words) < 20:
        await query.edit_message_text(
            "🎉 Hozircha barcha mavjud so‘zlar tugagan."
        )
        return

    context.user_data["exam_words"] = words.copy()
    context.user_data["exam_score"] = 0
    context.user_data["exam_index"] = 0

    await send_exam_question(query, context)


async def send_exam_question(query, context):

    words = context.user_data["exam_words"]
    index = context.user_data["exam_index"]

    if index >= len(words):

        score = context.user_data["exam_score"]
        user_id = query.from_user.id

        if score >= 16:
            add_xp(user_id, 200)

            cur.execute(
                "UPDATE users SET stage=stage+1 WHERE user_id=?",
                (user_id,)
            )
            db.commit()

            bonus = 100 if score == 20 else 0

            if bonus:
                add_xp(user_id, bonus)

            await query.edit_message_text(
                f"🎉 IMTIHON TUGADI!\n\n"
                f"Natija: {score}/20\n"
                f"✅ O‘tdingiz!\n\n"
                f"⭐ +200 XP\n"
                f"🚀 Keyingi 20 ta so‘z ochildi!"
            )

        else:

            await query.edit_message_text(
                f"📝 IMTIHON TUGADI\n\n"
                f"Natija: {score}/20\n"
                f"❌ O‘tmadingiz.\n\n"
                f"Kamida 16/20 kerak.\n"
                f"📚 So‘zlarni yana takrorlang."
            )

        return

    ru, correct = words[index]

    options = [correct]

    while len(options) < 4:
        fake = random.choice(words)[1]

        if fake not in options:
            options.append(fake)

    random.shuffle(options)

    keyboard = []

    for option in options:

        keyboard.append([
            InlineKeyboardButton(
                option,
                callback_data=f"exam_answer|{correct}|{option}"
            )
        ])

    await query.edit_message_text(
        f"📝 IMTIHON\n\n"
        f"Savol {index + 1}/20\n\n"
        f"🇷🇺 {ru}\n\n"
        f"To‘g‘ri tarjimani tanla:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# =========================================================
# CALLBACK
# =========================================================

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    data = query.data
    user_id = query.from_user.id

    if data == "today":
        await show_today_callback(query)
        return

    if data == "games":
        await games(update, context)
        return

    if data == "exam":
        await exam(update, context)
        return

    if data == "stats":
        await show_stats(query)
        return

    if data == "rank":
        await show_rank(query)
        return

    if data == "mistakes":
        await show_mistakes(query)
        return

    if data == "game_translate":
        await translation_game(query)
        return

    if data.startswith("answer|"):

        _, ru, correct, answer = data.split("|")

        if answer == correct:
            add_xp(user_id, 10)

            await query.edit_message_text(
                f"✅ To‘g‘ri!\n\n"
                f"🇷🇺 {ru}\n"
                f"🇺🇿 {correct}\n\n"
                f"⭐ +10 XP"
            )
        else:
            add_mistake(user_id, ru, correct)

            await query.edit_message_text(
                f"❌ Xato!\n\n"
                f"To‘g‘ri javob:\n"
                f"🇷🇺 {ru} — 🇺🇿 {correct}"
            )

        return

    if data.startswith("exam_answer|"):

        _, correct, answer = data.split("|")

        if answer == correct:
            context.user_data["exam_score"] += 1

        context.user_data["exam_index"] += 1

        await send_exam_question(query, context)
        return


# =========================================================
# MISTAKES
# =========================================================

def add_mistake(user_id, ru, uz):

    cur.execute(
        """
        SELECT count FROM mistakes
        WHERE user_id=? AND word=?
        """,
        (user_id, ru)
    )

    result = cur.fetchone()

    if result:
        cur.execute(
            """
            UPDATE mistakes
            SET count=count+1
            WHERE user_id=? AND word=?
            """,
            (user_id, ru)
        )
    else:
        cur.execute(
            """
            INSERT INTO mistakes(user_id,word,translation,count)
            VALUES(?,?,?,1)
            """,
            (user_id, ru, uz)
        )

    db.commit()


async def show_mistakes(query):

    user_id = query.from_user.id

    cur.execute(
        """
        SELECT word, translation, count
        FROM mistakes
        WHERE user_id=?
        ORDER BY count DESC
        LIMIT 20
        """,
        (user_id,)
    )

    mistakes = cur.fetchall()

    if not mistakes:
        await query.edit_message_text(
            "🎉 Hozircha xato so‘zlaringiz yo‘q!"
        )
        return

    text = "❌ ENG KO‘P XATO QILINGAN SO‘ZLAR\n\n"

    for word, translation, count in mistakes:
        text += f"🇷🇺 {word} — {translation} ({count}x)\n"

    await query.edit_message_text(text)


# =========================================================
# STATS
# =========================================================

async def show_stats(query):

    user_id = query.from_user.id
    user = get_user(user_id)

    level = user[1]
    xp = user[2]
    stage = user[3]
    streak = user[4]

    await query.edit_message_text(
        f"📊 SIZNING STATISTIKANGIZ\n\n"
        f"📚 Bosqich: {stage}\n"
        f"⭐ XP: {xp}\n"
        f"🏆 Level: {level}\n"
        f"🔥 Streak: {streak} kun\n\n"
        f"🎯 Keyingi maqsad: {level * 1000} XP"
    )


# =========================================================
# RANK
# =========================================================

async def show_rank(query):

    user_id = query.from_user.id
    user = get_user(user_id)

    xp = user[2]

    if xp < 1000:
        rank = "🥉 Beginner"
    elif xp < 3000:
        rank = "🥈 Learner"
    elif xp < 7000:
        rank = "🥇 Russian Student"
    elif xp < 15000:
        rank = "🔥 Russian Speaker"
    else:
        rank = "👑 Russian Master"

    await query.edit_message_text(
        f"🏆 SIZNING RANKINGIZ\n\n"
        f"{rank}\n\n"
        f"⭐ XP: {xp}"
    )


# =========================================================
# TODAY CALLBACK
# =========================================================

async def show_today_callback(query):

    user_id = query.from_user.id
    user = get_user(user_id)

    stage = user[3]

    start_index = (stage - 1) * 20
    words = WORDS[start_index:start_index + 20]

    text = f"📚 {stage}-BOSQICH\n\n"

    for i, (ru, uz) in enumerate(words, 1):
        text += f"{i}. {ru} — {uz}\n"

    await query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🎮 O‘yin", callback_data="games")],
            [InlineKeyboardButton("📝 Imtihon", callback_data="exam")]
        ])
    )


# =========================================================
# COMMANDS
# =========================================================

async def words_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await today(update, context)


async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_id = update.effective_user.id

    user = get_user(user_id)

    await update.message.reply_text(
        f"📊 Statistika\n\n"
        f"📚 Bosqich: {user[3]}\n"
        f"⭐ XP: {user[2]}\n"
        f"🏆 Level: {user[1]}\n"
        f"🔥 Streak: {user[4]}"
    )


# =========================================================
# START BOT
# =========================================================

def main():

    print("🇷🇺 Rus tili bot ishga tushdi...")

    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("today", today))
    app.add_handler(CommandHandler("words", words_command))
    app.add_handler(CommandHandler("stats", stats_command))

    app.add_handler(
        CallbackQueryHandler(button_handler)
    )

    app.run_polling()


if __name__ == "__main__":
    main()