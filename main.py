import os
import requests
from flask import Flask, request
import discord
from discord.ext import commands
import asyncio
import threading

# --- 환경 변수 및 설정 ---
TOKEN = os.environ.get("DISCORD_BOT_TOKEN")
CLIENT_ID = "1555799725083590676"
CLIENT_SECRET = os.environ.get("DISCORD_CLIENT_SECRET")
REDIRECT_URI = "https://discord-bot-ovr7.onrender.com/callback"
GUILD_ID = 1552247740585476188
ROLE_ID = 1556306587893633065

app = Flask(__name__)

# --- 디스코드 봇 설정 ---
intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} command(s)")
    except Exception as e:
        print(f"Failed to sync commands: {e}")

@bot.tree.command(name="인증", description="인증 버튼을 생성합니다.")
async def verify_command(interaction: discord.Interaction):
    auth_url = f"https://discord.com/api/oauth2/authorize?client_id={CLIENT_ID}&redirect_uri=https://discord-bot-ovr7.onrender.com/callback&response_type=code&scope=identify%20guilds.join"
    
    view = discord.ui.View()
    button = discord.ui.Button(label="인증하기", url=auth_url, style=discord.ButtonStyle.link)
    view.add_item(button)
    
    await interaction.response.send_message("아래 버튼을 눌러 인증을 진행해주세요!", view=view)

# --- 웹서버 (OAuth2 콜백 처리) ---
@app.route("/")
def home():
    return "Bot Server is Running!"

@app.route("/callback")
def callback():
    code = request.args.get("code")
    if not code:
        return "인증 코드가 없습니다.", 400

    data = {
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET,
        'grant_type': 'authorization_code',
        'code': code,
        'redirect_uri': REDIRECT_URI
    }
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    r = requests.post('https://discord.com/api/v10/oauth2/token', data=data, headers=headers)
    
    if r.status_code != 200:
        return f"토큰 요청 실패: {r.text}", 400

    token_data = r.json()
    access_token = token_data.get("access_token")

    user_headers = {'Authorization': f'Bearer {access_token}'}
    user_r = requests.get('https://discord.com/api/v10/users/@me', headers=user_headers)
    user_data = user_r.json()
    user_id = user_data.get("id")

    guild = bot.get_guild(GUILD_ID)
    if not guild:
        return "서버를 찾을 수 없습니다.", 500

    member = guild.get_member(int(user_id))
    role = guild.get_role(ROLE_ID)

    if member and role:
        asyncio.run_coroutine_threadsafe(member.add_roles(role), bot.loop)
        return "<h1>✅ 인증 성공!</h1><p>서버에 역할이 지급되었습니다. 이제 디스코드 창으로 돌아가셔도 됩니다.</p>"
    else:
        return "회원을 찾을 수 없거나 역할을 부여하지 못했습니다.", 400

def run_flask():
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

if __name__ == "__main__":
    t = threading.Thread(target=run_flask)
    t.start()
    bot.run(TOKEN)

