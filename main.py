from datetime import datetime
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
    500: 1513319309483573420,  # Örn: 500 puanda verilecek rol
    1000: 1513319170639528046   # Örn: 1000 puanda verilecek rol
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

# --- ACİL DURUM SENKRONİZASYON KOMUTU ---
@bot.command(name="sync")
async def sync(ctx):
    # Bu komutu sadece sen (admin) kullanabilirsin
    if ctx.author.id == 211215301059149824: # <--- Buraya KENDİ Discord ID'ni yaz!
        await bot.tree.sync()
        await ctx.send("✦ Slash komutları manuel olarak senkronize edildi!")
    else:
        await ctx.send("Bunu sadece botun sahibi kullanabilir.")

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

# --- BÖLÜM 2: AURA SİSTEMİ (TAMAMLANMIŞ) ---

# Kullanıcıların mesaj zamanlarını tutmak için bir sözlük
message_history = {}

@bot.event
async def on_message(message):
    if message.author.bot:
        await bot.process_commands(message)
        return

    user_id = message.author.id
    now = datetime.utcnow()

    # --- ANTI-SPAM VE CEZA SİSTEMİ ---
    if user_id not in message_history:
        message_history[user_id] = []

    # Son 60 saniyedeki mesajlarını filtrele
    message_history[user_id] = [t for t in message_history[user_id] if (now - t).total_seconds() < 60]
    message_history[user_id].append(now)

    # Eğer 60 saniyede 15 mesajdan fazla attıysa
    if len(message_history[user_id]) > 15:
        # Puan düş
        users_collection.update_one({"user_id": user_id}, {"$inc": {"aura_points": -50}})
        await message.channel.send(f"⚠️ {message.author.mention}, Aura kasma çaban karanlıkta kayboldu. Spam cezası: **-50 Aura**.")
        message_history[user_id] = [] 
        return 

    # --- NORMAL AURA SİSTEMİ ---
    user_data = users_collection.find_one_and_update(
        {"user_id": user_id},
        {"$inc": {"aura_points": 1}, "$set": {"last_seen": now}},
        upsert=True,
        return_document=True
    )

    new_points = user_data["aura_points"]

    # --- ROL KONTROL (Bu kısmı mutlaka ekle!) ---
    for threshold, role_id in ROLE_THRESHOLDS.items():
        if new_points >= threshold:
            role = message.guild.get_role(role_id)
            if role and role not in message.author.roles:
                try:
                    await message.author.add_roles(role)
                    await message.channel.send(f"🌌 {message.author.mention}, Aura seviyen yükseldi ve **{role.name}** rolünü kazandın!")
                except Exception as e:
                    print(f"Rol verme hatası: {e}")

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

# --- BÖLÜM 3: KEHANET SİSTEMİ (NİHAİ DÜZELTME) ---
@bot.tree.command(name="kehanet", description="REIGN sisteminden karanlık ve mistik bir fısıltı al.")
@app_commands.checks.cooldown(1, 60, key=lambda i: i.user.id) # 1 kullanıcı 60 saniyede 1 kez kullanabilir
async def kehanet(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=False)

    # 1. Veri Hazırlığı
    user_data = users_collection.find_one({"user_id": interaction.user.id})
    aura_points = user_data.get("aura_points", 0) if user_data else 0
    
    # Rolleri al, ama çok uzunsa botu yormamak için ilk 5 tanesini al
    user_roles = [role.name for role in interaction.user.roles if role.name != "@everyone"]
    roles_str = ", ".join(user_roles[:5])

    # 3. Mistik ve Rol Odaklı Prompt
    prompt = f"""
    Sen REIGN evreninin gölgelerde yaşayan, hafif alaycı, esrarengiz ve kadim bir kahinisin.
    Kullanıcı: {interaction.user.display_name}
    Aura Gücü: {aura_points}
    Sahip Olduğu Unvanlar/Roller: {roles_str}

    GÖREVİN: Kullanıcıya kısa, gizemli ve hafif tehditkar kehanet veya nispeten olumlu kehanet veya iç açıcı bir kehanet ver.

    KURALLAR (Sırasıyla Uygula, Kurallarımız çok katı değil, tamamen uymak zorunda değilsin.):
    1. YÜZ YÜZE SOHBET: Başlangıçta sanki karşında oturuyormuş gibi davran. (Örn: 'Ah.. yine sen mi? Hmm.. sanki.. sanki bir şeyler var.. garip.. çok garip..')
    2. ROL FARKINDALIĞI: Kullanıcının rollerini ve ismini incele.
       - 'Admin', 'Reign Şampiyonu' veya 'Kral' gibi unvanları varsa; dalkavukça, saygılı, hafif çekingen ama kadim bir dost gibi konuş.
       - 'Hanımefendi' veya benzeri zarif rolleri varsa; gizemli, hafif romantik ve büyüleyici bir ton kullan.
       - Hiçbir özel rolü yoksa; iğneleyici, 'sistemin gölgesindeki bir yabancı' gibi mesafeli konuş ve öneriler ver 'bu sunucuda vakit geçirmeye devam et, ben dahil insanlar seni sevecektir gibi..'.
       - REIGN sunucusunda neler yapabileceğini veya yapması gerektiğini söyle. (Örn: 'Belki de, benimle konuşarak veya REIGN'in arasına karışırsan kendine bir yer bulabilirsin, Kralımızla konuşmayı dene..')
    3. AURA YORUMU: Aura enerjisini (puanını) teknolojik terim kullanmadan, ruhsal bir seviye gibi betimle. (Örn: 0 puanlara yakınsa 'REIGN'de daha fazla vakit geçir.. enerjin az ama...', 50 puan için 'solgun bir kıvılcım', 500+ için 'gölgeleri titreten bir alev').
    4. İĞNELEME & GİZEM: İnsanların hayatına uyabilecek Barnum etkisi kullanan belirsiz nasihatler ver. (Örn: 'Peşinde olduğun o şey, aslında senden kaçıyor' veya 'Etrafındaki aptallar enerjini emiyor, yalnızlığı seç').
    5. TEKNOLOJİ YASAĞI: Asla matriks, veri, dijital, sistem, analiz gibi kelimeler kullanma!
    6. UZUNLUK: Cevabın en fazla 4-5 cümle olsun, kehanet vermeyi unutma.

    Doğrudan kullanıcıya hitap et ve kehanetini fısılda.
    """

    try:
        response = await ai_client.aio.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
        )
        kehanet_metni = response.text.strip()

        embed = discord.Embed(
            title="🌒 Karanlığın Fısıltısı",
            description=f"*{kehanet_metni}*",
            color=0x2b2b2b 
        )
        # BURASI DÜZELTİLDİ: 'f' eklendi
        embed.set_footer(text=f"REIGN Aura Kehaneti | Aura: {aura_points}")
        
        await interaction.followup.send(embed=embed)

    except Exception as e:
        # Hatanın ne olduğunu anlaman için loglara yazdırıyoruz
        print(f"DEBUG - Kehanet hatası: {e}") 
        await interaction.followup.send("Karanlık şu an sessizliğini koruyor... (Sistem bir anomaliyle karşılaştı, konsolu kontrol et.)")

# Hata yönetimi (cooldown için burası)
@kehanet.error
async def kehanet_error(interaction: discord.Interaction, error):
    if isinstance(error, app_commands.CommandOnCooldown):
        await interaction.followup.send(f"⏳ Karanlık şu an meşgul, kehanet için **{int(error.retry_after)} saniye** beklemen gerekiyor.")

# --- BÖLÜM 4: FRP / MACERA MOTORU ---

# FRP oturumlarını hafızada tutacağımız sözlük
frp_sessions = {}

# 1. FRP OYUN İÇİ BUTONLARI (Sonraki Tur ve Bitir)
class FRPGameView(discord.ui.View):
    def __init__(self, host_id, channel_id):
        super().__init__(timeout=None) # Zaman aşımı yok
        self.host_id = host_id
        self.channel_id = channel_id

    @discord.ui.button(label="Sonraki Tur", style=discord.ButtonStyle.primary, custom_id="frp_next", emoji="🎲")
    async def next_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.host_id:
            return await interaction.response.send_message("Sadece oyunu başlatan kişi turu ilerletebilir.", ephemeral=True)
        
        session = frp_sessions.get(self.channel_id)
        if not session or not session.get("is_active"):
            return await interaction.response.send_message("Aktif bir oyun bulunamadı.", ephemeral=True)
        
        if not session["current_actions"]:
            return await interaction.response.send_message("Hiç kimse hamle yapmadı! Oyuncuların `/do` komutunu kullanmasını bekle.", ephemeral=True)

        await interaction.response.defer()
        
        # Hamleleri birleştir
        hamleler_metni = "\n".join(session["current_actions"])
        
        prompt = f"""
        Sen REIGN evreninin Zindan Ustasısın (Dungeon Master). 
        Hikayenin şu anki durumu: {session['history']}
        
        Oyuncuların bu turdaki hamleleri:
        {hamleler_metni}
        
        Görev:
        1. Bu hamlelerin sonuçlarını mantıklı, acımasız ve karanlık bir şekilde anlat.
        2. Bazı hamleler başarılı olsun, bazıları başarısız (zarlara sen karar veriyormuşsun gibi düşün).
        3. Hikayeyi ilerlet ve onları yeni bir seçimle, tehlikeyle veya gizemle baş başa bırakıp "Ne yapıyorsunuz?" diye sor.
        4. Cevabın çok uzun olmasın (maksimum 3 paragraf). REIGN'in elit ve karanlık dilini koru. Teknolojik terim kullanma.
        """

        try:
            response = await ai_client.aio.models.generate_content(
                model='gemini-2.5-flash',
                contents=prompt,
            )
            dm_cevabi = response.text.strip()
            
            # Hafızayı güncelle (Eski hikayeyi silip yenisini özet olarak aklında tutsun ki şişmesin)
            session['history'] = dm_cevabi 
            session['current_actions'] = [] # Hamleleri sıfırla
            session['turn'] += 1

            embed = discord.Embed(
                title=f"📜 REIGN Macera Kayıtları - Tur {session['turn']}",
                description=f"{dm_cevabi}",
                color=0x8b0000 # Kan kırmızısı
            )
            embed.set_footer(text=f"Oyuncular: {', '.join(session['players'])} | Hamle yapmak için /do komutunu kullanın.")
            
            await interaction.followup.send(embed=embed, view=FRPGameView(self.host_id, self.channel_id))
            
            # Eski butonları devre dışı bırakmak istersen (isteğe bağlı)
            for child in self.children:
                child.disabled = True
            await interaction.message.edit(view=self)

        except Exception as e:
            print(f"FRP Hatası: {e}")
            await interaction.followup.send("Karanlık şu an zihnini okuyamıyor... (Sistem hatası)")

    @discord.ui.button(label="Macerayı Bitir", style=discord.ButtonStyle.danger, custom_id="frp_end", emoji="🛑")
    async def end_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.host_id:
            return await interaction.response.send_message("Sadece oyunu başlatan kişi bitirebilir.", ephemeral=True)
        
        if self.channel_id in frp_sessions:
            del frp_sessions[self.channel_id]
        
        embed = discord.Embed(title="Mühürlendi", description="Macera burada sona erdi. REIGN'in gölgeleri arasına karıştınız.", color=0x000000)
        await interaction.response.send_message(embed=embed)
        
        for child in self.children:
            child.disabled = True
        await interaction.message.edit(view=self)


# 2. FRP LOBİ BUTONLARI (Katıl ve Başlat)
class FRPLobbyView(discord.ui.View):
    def __init__(self, host_id, channel_id):
        super().__init__(timeout=600)
        self.host_id = host_id
        self.channel_id = channel_id

    @discord.ui.button(label="Katıl / Ayrıl", style=discord.ButtonStyle.secondary, custom_id="frp_join", emoji="🗡️")
    async def join_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        session = frp_sessions.get(self.channel_id)
        if not session or session.get("is_active"):
            return await interaction.response.send_message("Katılabilecek bir lobi yok veya oyun çoktan başladı.", ephemeral=True)
        
        user_name = interaction.user.display_name
        if user_name in session['players']:
            session['players'].remove(user_name)
            await interaction.response.send_message(f"Gölgelerden çekildin, {user_name}.", ephemeral=True)
        else:
            session['players'].append(user_name)
            await interaction.response.send_message(f"Masaya oturdun, {user_name}.", ephemeral=True)

    @discord.ui.button(label="Macerayı Başlat", style=discord.ButtonStyle.success, custom_id="frp_start", emoji="🔥")
    async def start_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.host_id:
            return await interaction.response.send_message("Sadece Macerayı kuran kişi başlatabilir.", ephemeral=True)
        
        session = frp_sessions.get(self.channel_id)
        if not session or len(session['players']) == 0:
            return await interaction.response.send_message("Masada kimse yok! Oyuncuların katılmasını bekleyin.", ephemeral=True)
        
        await interaction.response.defer()
        
        # Oyunu aktif et
        session["is_active"] = True
        oyuncu_listesi = ", ".join(session['players'])
        
        prompt = f"""
        Sen REIGN evreninin Zindan Ustasısın (Dungeon Master). 
        Bugün masanda şu oyuncular var: {oyuncu_listesi}
        
        Görev: Karanlık, gizemli, hafif fantastik veya Lovecraftian bir başlangıç hikayesi yaz.
        - Ortamı, kokuyu, tehlikeyi betimle. 
        - Oyuncuların kendini bir anda belanın ortasında veya gizemli bir yerde bulmasını sağla.
        - En sonda "Ne yapıyorsunuz?" diye sor.
        - Teknolojik terim kullanma, asil ve tekinsiz bir dil kullan.
        """

        try:
            response = await ai_client.aio.models.generate_content(
                model='gemini-2.5-flash',
                contents=prompt,
            )
            dm_cevabi = response.text.strip()
            session['history'] = dm_cevabi

            embed = discord.Embed(
                title="📜 REIGN Macerası Başlıyor...",
                description=f"{dm_cevabi}",
                color=0x8b0000
            )
            embed.set_footer(text=f"Kaderinizi seçin. Hamle yapmak için /do komutunu kullanın.")
            
            await interaction.followup.send(embed=embed, view=FRPGameView(self.host_id, self.channel_id))
            
            # Lobi butonlarını kapat
            for child in self.children:
                child.disabled = True
            await interaction.message.edit(view=self)

        except Exception as e:
            print(f"FRP Başlatma Hatası: {e}")
            await interaction.followup.send("Karanlık reddetti... (Sistem hatası)")

# 3. FRP KOMUTLARI
@bot.tree.command(name="frp_baslat", description="REIGN evreninde yeni bir FRP macerası (Text Adventure) başlat.")
async def frp_baslat(interaction: discord.Interaction):
    channel_id = interaction.channel_id
    
    # Kanalda zaten bir oyun var mı kontrol et
    if channel_id in frp_sessions:
        return await interaction.response.send_message("Bu kanalda zaten devam eden veya kurulan bir macera var. Önce onu bitirin.", ephemeral=True)

    # Yeni lobi oluştur
    frp_sessions[channel_id] = {
        "host_id": interaction.user.id,
        "is_active": False,
        "players": [],
        "current_actions": [],
        "history": "",
        "turn": 0
    }

    embed = discord.Embed(
        title="🎲 Masaya Davet",
        description=f"**{interaction.user.display_name}** yeni bir macera başlattı.\nKaderin zarları atılmak üzere. Katılmak için aşağıdaki butona basın. Herkes hazır olduğunda kurucu oyunu başlatabilir.",
        color=0x2b2b2b
    )
    
    await interaction.response.send_message(embed=embed, view=FRPLobbyView(interaction.user.id, channel_id))


@bot.tree.command(name="do", description="Aktif FRP macerasında karakterinin ne yapacağını belirle.")
@app_commands.describe(eylem="Örn: Kılıcımı çekip goblinin üstüne atlarım.")
async def do(interaction: discord.Interaction, eylem: str):
    session = frp_sessions.get(interaction.channel_id)
    
    if not session or not session.get("is_active"):
        return await interaction.response.send_message("Şu an devam eden bir macera yok veya lobi aşamasında.", ephemeral=True)
    
    if interaction.user.display_name not in session['players']:
        return await interaction.response.send_message("Oyunda değilsin! Dışarıdan müdahale edemezsin.", ephemeral=True)

    # Oyuncunun hamlesini kaydet
    hamle_metni = f"**{interaction.user.display_name}**: {eylem}"
    session['current_actions'].append(hamle_metni)

    await interaction.response.send_message(f"🎲 {hamle_metni}")

@bot.tree.command(name="frp_bitir", description="Aktif kanaldaki FRP macerasını tamamen sonlandırır ve hafızayı temizler.")
async def frp_bitir(interaction: discord.Interaction):
    channel_id = interaction.channel_id
    
    if channel_id not in frp_sessions:
        return await interaction.response.send_message("❌ Bu kanalda zaten devam eden aktif bir macera bulunmuyor.", ephemeral=True)
    
    session = frp_sessions[channel_id]
    
    if interaction.user.id != session["host_id"] and interaction.user.id != 211215301059149824:
        return await interaction.response.send_message("⚠️ Bu macerayı sadece oyunu kuran kişi veya sunucu sahibi sonlandırabilir.", ephemeral=True)
    
    del frp_sessions[channel_id]
    
    embed = discord.Embed(
        title="🛑 Kıyamet ve Sessizlik",
        description="REIGN Zindan Ustası günlüğü kapattı, mührü kırdı. Yaşanan tüm anılar ve gölgeler hafızadan tamamen silindi. Masadan kalkabilirsiniz.",
        color=0x000000
    )
    embed.set_footer(text="REIGN Macera Motoru Temizlendi")
    
    await interaction.response.send_message(embed=embed)

if __name__ == "__main__":
    keep_alive()  # Botu çalıştırmadan önce web sunucusunu aç
    bot.run(DISCORD_TOKEN)
