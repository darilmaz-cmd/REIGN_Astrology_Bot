from flask import Flask
from threading import Thread

app = Flask('')

@app.route('/')
def home():
    return "REIGN Bot Aktif!"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()

import discord
from discord.ext import commands, tasks
from discord import app_commands
from google import genai 
import re 
import os
from pymongo import MongoClient

mongo_uri = os.getenv('MONGO_URI')
client = MongoClient(mongo_uri)
db = client['ReignBotDB'] 
users_collection = db['Users']

# --- ROL EŞLEŞTİRME TABLOSU ---
# Puan Barajı : Rol ID (Sağ tıklayıp 'Kimliği Kopyala' dediğin ID'yi buraya yapıştır)
ROLE_THRESHOLDS = {
    100: 1513319309483573420,  # Örn: 100 puanda verilecek rol
    500: 1513319170639528046   # Örn: 500 puanda verilecek rol
}

# --- GİZLİ ANAHTARLAR ---
# Şifreleri artık kodun içine yazmıyoruz, sistemin kendi ayarlarından çekeceğiz
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Yapay Zeka Kurulumu 
ai_client = genai.Client(api_key=GEMINI_API_KEY)

# --- BOT KURULUMU VE İZİNLER ---
intents = discord.Intents.default()
intents.members = True 
intents.message_content = True

class ReignBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        await self.tree.sync()
        print("✦ Slash komutları REIGN sistemine senkronize edildi.")
        self.sabah_bulteni.start()

    @tasks.loop(hours=24)
    async def sabah_bulteni(self):
        pass 

    @sabah_bulteni.before_loop
    async def before_sabah_bulteni(self):
        await self.wait_until_ready()

bot = ReignBot()

@bot.event
async def on_ready():
    print(f'✦ {bot.user} REIGN evrenine giriş yaptı. Sistem stabil.')

# --- BÖLÜM 1: UYUM KOMUTU ---
@bot.tree.command(name="uyum", description="İki kişinin güneş ve yükselen burçlarına göre REIGN yapay zeka uyum analizi yapar.")
@app_commands.describe(hedef_kullanici="Uyumunu merak ettiğin kişiyi seç")
async def uyum(interaction: discord.Interaction, hedef_kullanici: discord.Member):
    await interaction.response.defer(ephemeral=False) 

    def burc_bul(member):
        gunes = "Bilinmiyor"
        yukselen = "Bilinmiyor"
        if not member or not getattr(member, 'roles', None):
            return gunes, yukselen
            
        burclar = ["koç", "boğa", "ikizler", "yengeç", "aslan", "başak", "terazi", "akrep", "yay", "oğlak", "kova", "balık"]
        
        for role in member.roles:
            # 1. Sembol kontrolü (yükselen mi güneş mi?)
            is_yukselen = "↑" in role.name or "⬆" in role.name or "up" in role.name.lower()
            
            # 2. Temizle: Sembolleri, boşlukları at, sadece harfleri bırak
            clean_name = re.sub(r'[^a-zçğıöşü]', '', role.name.lower())
            
            for b in burclar:
                if b in clean_name:
                    if is_yukselen:
                        yukselen = b.capitalize()
                    else:
                        gunes = b.capitalize()
        return gunes, yukselen

    kendi_gunes, kendi_yukselen = burc_bul(interaction.user)
    hedef_gunes, hedef_yukselen = burc_bul(hedef_kullanici)

    if (kendi_gunes == "Bilinmiyor" and kendi_yukselen == "Bilinmiyor") or (hedef_gunes == "Bilinmiyor" and hedef_yukselen == "Bilinmiyor"):
        await interaction.followup.send("⚠️ İşlem reddedildi. Analiz için iki taraftan birinin en azından Güneş burcunu seçmiş olması şarttır.")
        return

    prompt = f"""
    Sen asil, elit ve biraz karanlık bir atmosfere sahip olan REIGN isimli Discord sunucusunun zeki, laf sokan ve eğlenceli yapay zeka astroloğusun.
    Analiz edeceğin iki kişi var:
    1. Komutu çalıştıran kullanıcı: Güneş burcu {kendi_gunes}, Yükseleni {kendi_yukselen}.
    2. Hedef alınan kullanıcı: Güneş burcu {hedef_gunes}, Yükseleni {hedef_yukselen}.
    
    Görevlerin:
    1. Eğer bu iki kullanıcıdan birinin burcu 'Bilinmiyor' ise (özellikle yükselenleri), bu durumu çok ağır ve elit bir dille aşağıla.
    2. Ardından bu iki kişinin arkadaşlık veya aşk uyumunu analiz et. 
    ÖNEMLİ KURAL: Bu burçlar sana ait değil, kullanıcılara ait. Asla "Benim burcum" diye konuşma. Sen sadece dışarıdan bakan zeki bir yapay zekasın.
    Cevabın en fazla 2 paragraf olsun. Dili asla sıkıcı olmasın; elit, iğneleyici ve zekice olsun.
    """

    try:
        response = await ai_client.aio.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
        )
        
        yapay_zeka_cevabi = response.text[:4000] 
        
        embed = discord.Embed(
            title="🔮 REIGN Sistem Analizi: Karakter Uyumu", 
            description=f"**Sistem Yorumu:**\n\n{yapay_zeka_cevabi}", 
            color=0x000000
        ) 
        embed.add_field(name=f"{interaction.user.display_name}", value=f"Güneş: {kendi_gunes}\nYükselen: {kendi_yukselen}", inline=True)
        embed.add_field(name=f"{hedef_kullanici.display_name}", value=f"Güneş: {hedef_gunes}\nYükselen: {hedef_yukselen}", inline=True)
        embed.set_footer(text="REIGN Yapay Zeka Veritabanı")

        await interaction.followup.send(content=f"{interaction.user.mention} ✖️ {hedef_kullanici.mention}", embed=embed)
    
    except Exception as e:
        print(f"\n--- 🔴 YAPAY ZEKA BAĞLANTI HATASI ---")
        print(e)
        await interaction.followup.send("Sistemsel bir anomali oluştu. Lütfen botun konsoluna (terminal) bak.")

# --- BÖLÜM 2: AURA SİSTEMİ ---

@bot.event
async def on_message(message):
    # Botun kendi mesajlarını sayma, sadece komutları işlet
    if message.author.bot:
        await bot.process_commands(message)
        return

    # 1. Adım: Veritabanında güncelleme yap (upsert=True: yoksa oluştur, varsa güncelle)
    user_data = users_collection.find_one_and_update(
        {"user_id": message.author.id},
        {"$inc": {"aura_points": 1}},
        upsert=True,
        return_document=True
    )

    new_points = user_data["aura_points"]

    # 2. Adım: Rol Kontrolü
    # Kullanıcının puanına göre eşleşen rolü ver
    for threshold, role_id in ROLE_THRESHOLDS.items():
        if new_points >= threshold:
            role = message.guild.get_role(role_id)
            # Rol sunucuda varsa ve kullanıcıda bu rol henüz yoksa ver
            if role and role not in message.author.roles:
                try:
                    await message.author.add_roles(role)
                    await message.channel.send(f"🌌 {message.author.mention}, Aura seviyen yükseldi ve **{role.name}** rolünü kazandın!")
                except Exception as e:
                    print(f"Rol verme hatası: {e}")

    # Slash komutlarını ve prefix komutlarını bozmamak için bu satır şart
    await bot.process_commands(message)

# Klasik prefix (komut ön eki) ile çalışan aura komutu
@bot.command(name="aura")
async def aura(ctx):
    user_data = users_collection.find_one({"user_id": ctx.author.id})
    if user_data:
        puan = user_data.get("aura_points", 0)
        await ctx.send(f"🌌 {ctx.author.name}, şu anki Aura seviyen: **{puan}**.")
    else:
        await ctx.send("Henüz Aura'n kaydedilmemiş, biraz daha aktif olmalısın.")

if __name__ == "__main__":
    keep_alive()  # Botu çalıştırmadan önce web sunucusunu aç
    bot.run(DISCORD_TOKEN)
