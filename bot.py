import discord
from discord.ext import commands
import aiosqlite
import os
from datetime import datetime

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

# ================== Settings ==================
TOKEN = os.getenv("DISCORD_TOKEN")
TARGET_BOT_ID = int(os.getenv("TARGET_BOT_ID", "0"))
POINTS_PER_MENTION = int(os.getenv("POINTS_PER_MENTION", 10))

if not TOKEN or TARGET_BOT_ID == 0:
    print("❌ Missing configuration!")
    exit(1)

# ================== Database ==================
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

# ================== Events ==================
@bot.event
async def on_ready():
    await init_db()
    print(f"✅ Bot {bot.user} is now online!")
    print(f"🎯 Target Bot ID: {TARGET_BOT_ID}")
    print(f"⭐ Points per mention: {POINTS_PER_MENTION}")

@bot.event
async def on_message(message: discord.Message):
    if message.author.id != TARGET_BOT_ID:
        return
    if not message.mentions:
        return

    count = len(message.mentions)
    for user in message.mentions:
        await add_points(str(user.id), user.name)
    
    print(f"✅ {count} user(s) were mentioned and received points.")
    await bot.process_commands(message)

# ================== Commands ==================
@bot.command(name="points")
async def show_points(ctx, member: discord.Member = None):
    if member is None:
        member = ctx.author
    
    async with aiosqlite.connect("points.db") as db:
        async with db.execute("SELECT points FROM users WHERE user_id = ?", (str(member.id),)) as cursor:
            row = await cursor.fetchone()
            points = row[0] if row else 0
    
    await ctx.send(f"**{member.mention}** has **{points}** points.")


@bot.command(name="leaderboard", aliases=["lb", "top"])
async def leaderboard(ctx):
    async with aiosqlite.connect("points.db") as db:
        async with db.execute("""
            SELECT username, points FROM users 
            ORDER BY points DESC LIMIT 15
        """) as cursor:
            data = await cursor.fetchall()
    
    if not data:
        return await ctx.send("No points have been recorded yet.")
    
    embed = discord.Embed(title="🏆 Points Leaderboard", color=0x00ff00)
    for i, (username, points) in enumerate(data, 1):
        embed.add_field(name=f"#{i} • {username}", value=f"**{points}** points", inline=False)
    
    await ctx.send(embed=embed)


@bot.command(name="addpoints")
@commands.has_permissions(administrator=True)
async def add_manual_points(ctx, member: discord.Member, amount: int):
    await add_points(str(member.id), member.name, amount)
    await ctx.send(f"✅ Added **{amount}** points to {member.mention}.")


# ================== Run the bot ==================
bot.run(TOKEN)
