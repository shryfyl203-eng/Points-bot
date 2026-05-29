import discord
from discord.ext import commands
import aiosqlite
import os
from datetime import datetime

# ================== تنظیمات intents ==================
intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

# ================== ⚠️ جاهایی که باید جایگزین کنی ⚠️ ==================

TOKEN = os.getenv("MTUwOTE0NDU5MzM5OTE1Njc3OA.G8ykWp.k7hTgQpnvSX8kElC3hfLAD_-Ig7o__Q7EIL4_E")                    # *** این را دست نزن ***

TARGET_BOT_ID = int(os.getenv("725721249652670555", "0")) # *** آیدی بات رقیب را در Railway وارد کن ***

POINTS_PER_MENTION = int(os.getenv("POINTS_PER_MENTION", 10))  # *** امتیاز هر منشن (پیش‌فرض ۱۰) ***

# =====================================================================

if not TOKEN:
    print("❌ توکن پیدا نشد! متغیر DISCORD_TOKEN را در Railway تنظیم کنید.")
    exit(1)

if TARGET_BOT_ID == 0:
    print("⚠️ WARNING: TARGET_BOT_ID هنوز تنظیم نشده است!")

# ================== دیتابیس ==================
async def init_db():
    async with aiosqlite.connect("points.db") as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id TEXT PRIMARY KEY,
                username TEXT,
                points INTEGER DEFAULT 0,
                last_update TEXT
            )
        """)
        await db.commit()

async def add_points(user_id: str, username: str, amount: int = POINTS_PER_MENTION):
    async with aiosqlite.connect("points.db") as db:
        await db.execute("""
            INSERT INTO users (user_id, username, points, last_update)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET 
                points = points + ?,
                username = ?,
                last_update = ?
        """, (user_id, username, amount, datetime.now().strftime("%Y-%m-%d %H:%M"), 
              amount, username, datetime.now().strftime("%Y-%m-%d %H:%M")))
        await db.commit()

# ================== وقتی بات آنلاین شد ==================
@bot.event
async def on_ready():
    await init_db()
    print(f"✅ بات {bot.user} با موفقیت آنلاین شد!")
    print(f"🎯 بات هدف (رقیب): {TARGET_BOT_ID}")
    print(f"⭐ هر منشن = {POINTS_PER_MENTION} امتیاز")

# ================== دریافت پیام‌ها ==================
@bot.event
async def on_message(message: discord.Message):
    if message.author.id != TARGET_BOT_ID:
        return
    if not message.mentions:
        return

    count = len(message.mentions)
    for user in message.mentions:
        await add_points(str(user.id), user.name)
    
    print(f"✅ {count} نفر منشن شدند و امتیاز گرفتند.")
    await bot.process_commands(message)

# ================== دستورات ==================
@bot.command(name="امتیاز")
async def show_points(ctx, member: discord.Member = None):
    if member is None:
        member = ctx.author
    
    async with aiosqlite.connect("points.db") as db:
        async with db.execute("SELECT points FROM users WHERE user_id = ?", (str(member.id),)) as cursor:
            row = await cursor.fetchone()
            points = row[0] if row else 0
    
    await ctx.send(f"**{member.mention}** دارای **{points}** امتیاز است.")


@bot.command(name="لیدربورد", aliases=["رتبه", "leaderboard"])
async def leaderboard(ctx):
    async with aiosqlite.connect("points.db") as db:
        async with db.execute("SELECT username, points FROM users ORDER BY points DESC LIMIT 15") as cursor:
            data = await cursor.fetchall()
    
    if not data:
        return await ctx.send("هنوز امتیازی ثبت نشده.")
    
    embed = discord.Embed(title="🏆 لیدربورد امتیازات", color=0x00ff00)
    for i, (username, points) in enumerate(data, 1):
        embed.add_field(name=f"#{i} • {username}", value=f"**{points}** امتیاز", inline=False)
    
    await ctx.send(embed=embed)


# ================== دستور اضافه کردن دستی امتیاز (ادمین) ==================
@bot.command(name="اضافه")
@commands.has_permissions(administrator=True)
async def add_manual_points(ctx, member: discord.Member, amount: int):
    await add_points(str(member.id), member.name, amount)
    await ctx.send(f"✅ به {member.mention} مقدار **{amount}** امتیاز اضافه شد.")


# ================== اجرای بات ==================
bot.run(MTUwOTE0NDU5MzM5OTE1Njc3OA.G8ykWp.k7hTgQpnvSX8kElC3hfLAD_-Ig7o__Q7EIL4_E)