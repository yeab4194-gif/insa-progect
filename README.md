# SecureAuth — Secure User Authentication System

A full-featured authentication system built with Python / Flask, ready for local development and cloud deployment on Render.

## Features

| Feature | Details |
|---|---|
| **Registration** | Username, email, password with real-time strength checker |
| **Password strength** | 5-criteria checker: length, uppercase, lowercase, digits, special chars |
| **Password hashing** | bcrypt with cost factor 12 (unique salt per password) |
| **Brute-force protection** | 5 failed attempts → 15-minute account lockout |
| **Two-Factor Auth (2FA)** | 6-digit OTP sent by email, expires in 10 minutes |
| **Admin panel** | User management, unlock accounts, full security event log |
| **Security logging** | Every event persisted: login, fail, lock, OTP, logout, register |

---

## Run Locally

### 1. Install Python 3.10+
Download from https://www.python.org/downloads/  
**Check "Add Python to PATH"** during installation.

### 2. Clone / download the project
```
cd "C:\Users\dell\Desktop\INSA PROGECT"
```

### 3. (Recommended) Create a virtual environment
```
python -m venv venv
venv\Scripts\activate
```

### 4. Install dependencies
```
pip install -r requirements.txt
```

### 5. Set environment variables (optional — for real email)
```
set MAIL_USERNAME=your@gmail.com
set MAIL_PASSWORD=your-app-password
set MAIL_DEFAULT_SENDER=your@gmail.com
```
> Use a Gmail **App Password**, not your regular password.  
> Without this, the OTP is shown on-screen in a flash message (dev mode).

### 6. Create the admin user
```
python seed_admin.py
```

### 7. Start the development server
```
python app.py
```
Open http://localhost:5000

### Default admin credentials
| Field | Value |
|---|---|
| Username | `admin` |
| Password | `Admin@1234!` |

> Change this password immediately after first login.

---

## Deploy on Render

### Prerequisites
- A free account at https://render.com
- Your project pushed to a GitHub repository

### Step-by-step

**1. Push to GitHub**
```
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO.git
git push -u origin main
```

**2. Create a new Web Service on Render**
- Go to https://dashboard.render.com → **New → Web Service**
- Connect your GitHub repo
- Render auto-detects `render.yaml` — or fill in manually:

| Field | Value |
|---|---|
| Runtime | Python |
| Build Command | `pip install -r requirements.txt` |
| Start Command | `gunicorn app:app` |

**3. Add environment variables** in the Render dashboard → Environment tab:

| Key | Value |
|---|---|
| `SECRET_KEY` | A long random string (use Render's "Generate" button) |
| `FLASK_DEBUG` | `false` |
| `MAIL_USERNAME` | your Gmail address |
| `MAIL_PASSWORD` | your Gmail App Password |
| `MAIL_DEFAULT_SENDER` | your Gmail address |

**4. (Optional) Add a PostgreSQL database**
- Render dashboard → **New → PostgreSQL**
- Link it to your web service — Render sets `DATABASE_URL` automatically
- The app reads `DATABASE_URL` and uses it instead of SQLite

**5. Deploy**
- Click **Deploy** — Render installs dependencies and starts Gunicorn
- Your app will be live at `https://your-service-name.onrender.com`

**6. Seed the admin user on Render**
- Go to your service → **Shell** tab
- Run: `python seed_admin.py`

---

## Project Structure

```
.
├── app.py              # App factory + module-level app variable for Gunicorn
├── config.py           # All configuration (reads from environment variables)
├── extensions.py       # Flask extension instances
├── models.py           # User and LoginLog database models
├── seed_admin.py       # One-time admin user creation script
├── requirements.txt    # Pinned Python dependencies
├── Procfile            # Gunicorn start command (web: gunicorn app:app)
├── render.yaml         # Render deployment config
├── .gitignore          # Excludes *.db, .env, __pycache__, venv/
│
├── routes/
│   ├── auth.py         # Register, login, OTP verify, logout
│   ├── admin.py        # Admin dashboard, user management, logs
│   └── main.py         # Home/dashboard page
│
├── utils/
│   ├── password.py     # Strength checker + bcrypt hashing
│   ├── otp.py          # OTP generation, email delivery, verification
│   └── logging.py      # Security event logger
│
├── templates/
│   ├── base.html
│   ├── index.html
│   ├── login.html
│   ├── register.html
│   ├── verify_otp.html
│   └── admin/
│       ├── dashboard.html
│       ├── users.html
│       └── logs.html
│
└── static/
    └── css/style.css
```

---

## Security Notes

- Passwords hashed with **bcrypt** (cost 12) — never stored in plain text
- OTP generated with Python `secrets` module — cryptographically secure
- OTP comparison uses `secrets.compare_digest` — timing-attack safe
- Brute-force lockout stored in DB — survives server restarts
- `SECRET_KEY` and credentials loaded from environment variables — never hardcoded

---

## Configuration Reference

| Env Variable | Default | Description |
|---|---|---|
| `SECRET_KEY` | (insecure default) | Flask session signing key — **always override in production** |
| `DATABASE_URL` | SQLite file | Full DB connection string |
| `MAX_LOGIN_ATTEMPTS` | 5 (in config.py) | Failed attempts before lockout |
| `LOCKOUT_DURATION_MINUTES` | 15 (in config.py) | Lockout duration |
| `OTP_EXPIRY_MINUTES` | 10 (in config.py) | OTP validity window |
| `MAIL_SERVER` | smtp.gmail.com | SMTP server |
| `MAIL_PORT` | 587 | SMTP port |
| `MAIL_USERNAME` | — | SMTP username |
| `MAIL_PASSWORD` | — | SMTP password |
