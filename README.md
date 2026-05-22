# 🎬 Kino Bot — Production Telegram Bot

Professional Telegram bot: kino qidirish, admin panel, obuna tekshiruvi va ko'p narsa!

## 📁 Loyiha Strukturasi

```
kino_bot/
├── main.py                  # Bot ishga tushirish nuqtasi
├── config.py                # Konfiguratsiya va sozlamalar
├── database.py              # SQLite ma'lumotlar bazasi
├── requirements.txt         # Python kutubxonalar
├── .env                     # Muhit o'zgaruvchilari (gitga qo'shma!)
├── .env.example             # .env namunasi
├── handlers/
│   ├── __init__.py
│   ├── user.py              # Foydalanuvchi handlerlari
│   ├── admin.py             # Admin panel handlerlari
│   ├── subscription.py      # Obuna tekshiruvi
│   └── search.py            # Qidiruv tizimi
├── keyboards/
│   ├── __init__.py
│   ├── inline.py            # Inline klaviaturalar
│   └── reply.py             # Reply klaviaturalar
├── middlewares/
│   ├── __init__.py
│   └── subscription.py      # Obuna middleware
└── utils/
    ├── __init__.py
    ├── decorators.py        # Admin tekshiruv decoratorlari
    └── helpers.py           # Yordamchi funksiyalar
```

## ⚙️ O'rnatish

```bash
git clone <repo_url>
cd kino_bot
python -m venv venv
source venv/bin/activate      # Linux/Mac
venv\Scripts\activate         # Windows
pip install -r requirements.txt
cp .env.example .env
# .env faylini to'ldiring
python main.py
```

## 🚀 Deployment (Render.com)

1. GitHub'ga yuklang
2. render.com da yangi "Background Worker" yarating
3. Environment variables qo'shing (.env.example ga qarang)
4. Deploy bosing

## 🚀 Deployment (VPS)

```bash
# systemd service
sudo nano /etc/systemd/system/kinobot.service
sudo systemctl enable kinobot
sudo systemctl start kinobot
```
