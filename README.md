# Pishiq Bot — shaxsiy kirim-chiqim hisobchi

Telegram orqali ishlaydigan shaxsiy moliya kuzatuv boti. Interfeys to'liq o'zbek tilida, foydalanuvchi
uchun tez va qulay tranzaksiya kiritishga mo'ljallangan.

## Xususiyatlar

- ➕ Kirim / ➖ Chiqim — bir necha bosishda tranzaksiya qo'shish
- 💵 Naqd va 💳 Karta bo'yicha alohida balanslar, tranzaksiyalardan hisoblanadi (saqlanmaydi)
- 🔄 Naqd ↔ Karta pul o'tkazmalari (kirim/chiqim hisoblanmaydi, umumiy balansga ta'sir qilmaydi)
- 📊 Davr bo'yicha hisobotlar (bugun/kecha/hafta/oy/o'tgan oy/ixtiyoriy sana) + kategoriya bo'yicha taqsimot
- 📋 Filtrlanadigan va sahifalanadigan tranzaksiyalar tarixi, tahrirlash va o'chirish
- ⚙️ Foydalanuvchi kategoriyalarini yaratish/o'zgartirish/o'chirish (ishlatilgan kategoriya yumshoq o'chiriladi)
- Tez kiritish: `- 150000 oziq-ovqat karta` yoki `+ 500000 freelance karta`
- Faqat bitta ruxsat etilgan Telegram foydalanuvchisi uchun

## Arxitektura

```
app/
├── bot/
│   ├── handlers/       Telegram-ga bog'liq logika (FSM oqimlari, xabarlar)
│   ├── keyboards/       Inline/reply klaviaturalar
│   ├── middlewares/      Auth, DB session, foydalanuvchi konteksti
│   └── states/           aiogram FSM holatlari
├── database/
│   ├── models/           SQLAlchemy 2.x modellar (User, Category, Transaction)
│   ├── repositories/      Sof so'rovlar qatlami (biznes qoidalarisiz)
│   └── session.py
├── services/              Biznes logika: balans, tranzaksiya, hisobot, kategoriya, tez kiritish parseri
├── utils/                 Pul formatlash, sana yordamchilari, xatoliklar
├── config.py              Pydantic-settings orqali .env validatsiyasi
└── main.py                Bot kirish nuqtasi
migrations/                 Alembic migratsiyalari
tests/                       Biznes logika testlari (pytest + in-memory SQLite)
```

**Muhim dizayn qarorlari:**

- **Pul hech qachon float emas.** `amount` butun son (so'm) sifatida saqlanadi; barcha arifmetika butun sonlar bilan.
- **Balans hech qachon alohida saqlanmaydi** — har doim `Transaction` jadvalidan real vaqtda hisoblanadi, shu sababli u hech qachon nomuvofiq holatga tushmaydi.
- **O'tkazmalar kirim/chiqim emas** — alohida `type=transfer` va `transfer_from`/`transfer_to` ustunlari orqali ifodalanadi, hisobot va balans hisob-kitoblaridan chiqarib tashlanadi (faqat naqd/karta orasida ko'chiriladi).
- **Kategoriya o'chirish xavfsiz** — agar kategoriyada tranzaksiyalar bo'lsa, u yumshoq o'chiriladi (`is_active=False`), aks holda butunlay o'chiriladi.
- **Tez kiritish parseri deterministik** — `+/- summa kategoriya [naqd|karta] [izoh]` formatini tan oladi; kategoriya yoki to'lov usuli aniq bo'lmasa, botni hech qachon taxmin qilmaydi — foydalanuvchidan tanlashni so'raydi.

## O'rnatish (lokal, Docker bilan)

1. `.env` faylini yarating:

```bash
cp .env.example .env
```

2. `.env` faylida quyidagilarni to'ldiring:

```env
BOT_TOKEN=<BotFather bergan token>
DATABASE_URL=postgresql+asyncpg://pishiqbot:pishiqbot@db:5432/pishiqbot
ALLOWED_TELEGRAM_USER_ID=<sizning Telegram ID'ingiz>
TIMEZONE=Asia/Tashkent
```

Telegram ID'ingizni bilish uchun [@userinfobot](https://t.me/userinfobot) ga yozing.

3. Ishga tushiring:

```bash
docker compose up --build
```

Bu Postgres'ni ko'taradi, `migrate` xizmati Alembic migratsiyalarini qo'llaydi, so'ng bot ishga tushadi.

## Migratsiyalar

Docker Compose ichida `migrate` xizmati avtomatik ishlaydi. Qo'lda ishga tushirish uchun:

```bash
docker compose run --rm migrate
```

Yangi migratsiya yaratish (model o'zgargandan keyin):

```bash
docker compose run --rm bot alembic revision --autogenerate -m "tavsif"
```

## Lokal ishga tushirish (Dockersiz)

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt
```

`.env` da `DATABASE_URL` ni lokal Postgres'ga (yoki `db` xost o'rniga `localhost`) moslang, so'ng:

```bash
alembic upgrade head
python -m app.main
```

## Testlarni ishga tushirish

Testlar biznes logikaga (services/repositories) qaratilgan va xotiradagi SQLite'da ishlaydi — alohida DB kerak emas:

```bash
pip install -r requirements-dev.txt
pytest
```

Qamrov: kirim/chiqim qo'shish, naqd/karta/umumiy balans hisob-kitobi, ikki yo'nalishdagi o'tkazmalar,
tranzaksiyani tahrirlash/o'chirish, oylik hisobot va kategoriya bo'yicha taqsimot, sana oralig'i chegaralari,
ruxsatsiz foydalanuvchini rad etish, va noto'g'ri/manfiy/nol summalarni validatsiya qilish.

## Fly.io ga joylash

Loyiha `fly.toml` bilan birga keladi — bot HTTP server emas (long-polling), shuning uchun
`fly.toml`da `[http_service]` bo'limi yo'q, faqat uzluksiz ishlaydigan worker sifatida tavsiflangan.

1. **flyctl o'rnatish va kirish** (agar hali qilinmagan bo'lsa):

   ```bash
   flyctl auth login
   ```

2. **Ilovani yaratish** (`fly.toml`dagi `app` nomi band bo'lsa, uni o'zgartiring):

   ```bash
   flyctl apps create pishiqbot
   ```

3. **Postgres yaratish va bog'lash** — bu `DATABASE_URL` maxfiy o'zgaruvchisini avtomatik o'rnatadi:

   ```bash
   flyctl postgres create --name pishiqbot-db --region waw --initial-cluster-size 1 --vm-size shared-cpu-1x --volume-size 1
   flyctl postgres attach pishiqbot-db --app pishiqbot
   ```

   (`fly postgres attach` `postgres://...` formatida beradi — ilova buni avtomatik
   `postgresql+asyncpg://...`ga o'giradi, qo'lda o'zgartirish shart emas.)

4. **Maxfiy o'zgaruvchilarni o'rnatish:**

   ```bash
   flyctl secrets set BOT_TOKEN=<sizning tokeningiz> ALLOWED_TELEGRAM_USER_ID=<sizning Telegram ID'ingiz> --app pishiqbot
   ```

5. **Joylash:**

   ```bash
   flyctl deploy --app pishiqbot
   ```

   Deploy paytida `release_command = "alembic upgrade head"` avtomatik ishlaydi, shuning
   uchun migratsiyalar har bir joylashda o'zi yangilanadi.

6. **Tekshirish:**

   ```bash
   flyctl logs --app pishiqbot
   ```

   Loglarda `Run polling for bot @...` qatorini ko'rsangiz, bot ishga tushgan.

## Muhit o'zgaruvchilari

| O'zgaruvchi | Tavsif |
|---|---|
| `BOT_TOKEN` | BotFather bergan token |
| `DATABASE_URL` | Async SQLAlchemy DSN, masalan `postgresql+asyncpg://user:pass@host:5432/db` |
| `ALLOWED_TELEGRAM_USER_ID` | Botdan foydalanishga ruxsat etilgan yagona Telegram user ID |
| `TIMEZONE` | Standart: `Asia/Tashkent` |

Ilova ishga tushganda konfiguratsiya validatsiya qilinadi — noto'g'ri yoki yo'q qiymatlar bo'lsa, bot xato bilan darhol to'xtaydi (jim xato yo'q).

## Xavfsizlik

- Faqat `ALLOWED_TELEGRAM_USER_ID` bilan mos keluvchi foydalanuvchi botdan foydalana oladi; boshqa barcha xabarlar `AuthMiddleware` tomonidan rad etiladi.
- Texnik xatolar (stack trace, DB xatolari) hech qachon foydalanuvchiga ko'rsatilmaydi — faqat umumiy o'zbekcha xabar (`❌ Xatolik yuz berdi...`), texnik tafsilotlar serverga log qilinadi.
- Bot tokeni, DB ma'lumotlari va boshqa maxfiy sozlamalar faqat `.env` orqali beriladi va hech qachon xabarlarga chiqarilmaydi.

## Kelajakdagi kengaytirishlar uchun tayyorlangan

Joriy MVP quyidagilarni amalga oshirmaydi, lekin arxitektura ularni keyinchalik qo'shishga qulay:

- Ko'p valyuta, bir nechta bank hisoblari, byudjetlar, takrorlanuvchi tranzaksiyalar
- Jamg'arma maqsadlari, CSV/Excel eksport, grafiklar
- AI yordamida avtomatik kategoriyalash, rejalashtirilgan hisobotlar

Bular uchun `services/` qatlami allaqachon Telegram handlerlardan ajratilgan, shuning uchun yangi funksiyalar
mavjud oqimlarni buzmasdan qo'shilishi mumkin.
