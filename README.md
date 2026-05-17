# SecureAuth — Secure User Authentication System

A full-featured authentication system built with Python/Flask.

## Features

| Feature | Details |
|---|---|
| **Registration** | Username, email, password with real-time strength checker |
| **Password strength** | 5-criteria checker: length, uppercase, lowercase, digits, special chars |
| **Password hashing** | bcrypt with cost factor 12 (salt embedded) |
| **Brute-force protection** | 5 failed attempts → 15-minute account lockout |
| **Two-Factor Auth (2FA)** | 6-digit OTP sent by email, expires in 10 minutes |
| **Admin panel** | User management, unlock accounts, view all security logs |
| **Security logging** | Every event (login, fail, lock, OTP, logout, register) is persisted |

---

## Quick Start

### 1. Install Python
Download from https://www.python.org/downloads/ (Python 3.10+).
Make sure to check **"Add Python to PATH"** during installation.

### 2. Install dependencies
Open a terminal in this folder and run:
```
pip install -r requirements.txt
```

### 3. Configure email (optional but recommended)
Set environment variables before running:
```
set MAIL_USERNAME=your@gmail.com
set MAIL_PASSWORD=your-app-password
set MAIL_DEFAULT_SENDER=your@gmail.com
```
> For Gmail, use an **App Password** (not your regular password).
> If email is not configured, the OTP will be shown in a flash message on screen (dev mode).

### 4. Create the admin user
```
python seed_admin.py
```
Default admin credentials:
- Username: `admin`
- Password: `Admin@1234!`

### 5. Run the application
```
python app.py
```
Open http://localhost:5000 in your browser.

---

## Project Structure

```
INSA PROGECT/
├── app.py              # Application factory & entry point
├── config.py           # All configuration (timeouts, limits, SMTP, etc.)
├── extensions.py       # Flask extension instances
├── models.py           # User and LoginLog database models
├── seed_admin.py       # One-time admin user creation script
├── requirements.txt    # Python dependencies
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
│   ├── base.html       # Shared layout (navbar, flash messages)
│   ├── index.html      # User dashboard
│   ├── login.html      # Login form
│   ├── register.html   # Registration form with live strength meter
│   ├── verify_otp.html # OTP entry form
│   └── admin/
│       ├── dashboard.html
│       ├── users.html
│       └── logs.html
│
└── static/
    └── css/
        └── style.css   # Full UI stylesheet
```

---

## Security Design

### Password Hashing
Passwords are hashed with **bcrypt** (cost factor 12). bcrypt automatically generates and embeds a unique salt per password, making rainbow-table attacks infeasible.

### Brute-Force Protection
- After **5 consecutive failed login attempts**, the account is locked for **15 minutes**.
- The lockout timer is stored in the database, so it survives server restarts.
- Admins can manually unlock accounts from the admin panel.

### Two-Factor Authentication
- After correct username/password, a **6-digit numeric OTP** is generated using Python's `secrets` module (cryptographically secure).
- The OTP is sent to the user's registered email and expires in **10 minutes**.
- Comparison uses `secrets.compare_digest` to prevent timing attacks.

### Session Security
- Sessions are server-side (Flask signed cookies with `SECRET_KEY`).
- The pending 2FA state is stored in the session, not the URL.
- Sessions expire after 30 minutes of inactivity.

---

## Configuration Reference (`config.py`)

| Setting | Default | Description |
|---|---|---|
| `MAX_LOGIN_ATTEMPTS` | 5 | Failed attempts before lockout |
| `LOCKOUT_DURATION_MINUTES` | 15 | Lockout duration |
| `OTP_EXPIRY_MINUTES` | 10 | OTP validity window |
| `OTP_LENGTH` | 6 | OTP digit count |
| `SECRET_KEY` | (change this) | Flask session signing key |

---

## Production Checklist

- [ ] Set a strong random `SECRET_KEY` environment variable
- [ ] Configure real SMTP credentials (`MAIL_USERNAME`, `MAIL_PASSWORD`)
- [ ] Switch from SQLite to PostgreSQL (`DATABASE_URL` env var)
- [ ] Run behind HTTPS (nginx + Let's Encrypt)
- [ ] Set `debug=False` in `app.py`
- [ ] Change the default admin password after first login
