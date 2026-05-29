import discord
from discord.ext import commands
import aiosqlite
from datetime import datetime

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

TARGET_BOT_ID = 725721249652670555
POINTS_PER_MENTION = 10

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
        """, (user_id, username, amount, datetime.now().strftime("%Y-%m-%d %H:%M"), amount, username, datetime.now().strftime("%Y-%m-%d %H:%M")))
        await db.commit()

@bot.event
async def on_ready():
    await init_db()
    print(f'✅ بات {bot.user} آنلاین شد!')

@bot.event
async def on_message(message: discord.Message):
    if message.author.id != TARGET_BOT_ID:
        return
    if not message.mentions:
        return

    for user in message.mentions:
        await add_points(str(user.id), user.name)
    
    print(f"{len(message.mentions)} نفر امتیاز گرفتند.")
    await bot.process_commands(message)

@bot.command(name="امتیاز")
async def show_points(ctx, member: discord.Member = None):
    if member is None: member = ctx.author
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
    
    embed = discord.Embed(title="🏆 لیدربورد", color=0x00ff00)
    for i, (username, points) in enumerate(data, 1):
        embed.add_field(name=f"#{i} • {username}", value=f"**{points}** امتیاز", inline=False)
    await ctx.send(embed=embed)

bot.run("YOUR_TOKEN_HERE")   # بعداً عوض می‌کنیم