# MindBridge

MindBridge is a role-based mental-health education prototype for children,
parents, teachers and counsellors.

## Features

- Secure password hashing
- PostgreSQL database storage
- Login and role-based protected pages
- Child learning video and booklet
- Learning progress tracking
- Feelings check-ins and support requests
- Parent/teacher monitoring
- Active/inactive child accounts
- Counsellor advice

## Project structure

```text
MindBridge_PostgreSQL/
├── main.py
├── database.py
├── models.py
├── schemas.py
├── auth.py
├── requirements.txt
├── .env.example
├── templates/
└── static/
```

## 1. Create the PostgreSQL database

In Terminal:

```bash
createdb mindbridge
```

If that command is unavailable, use:

```bash
psql postgres
```

Then run:

```sql
CREATE DATABASE mindbridge;
\q
```

## 2. Configure the database

Copy the example environment file:

```bash
cp .env.example .env
```

The default database address is:

```text
postgresql+psycopg2://mac@localhost:5432/mindbridge
```

Change `mac` if your PostgreSQL username is different.

For a password-protected PostgreSQL account, use:

```text
postgresql+psycopg2://USERNAME:PASSWORD@localhost:5432/mindbridge
```

## 3. Install and run

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload
```

Open:

```text
http://127.0.0.1:8000
```

Do not open this version with Live Server. FastAPI serves the pages.

## Demo accounts

All demo passwords are `1234`.

- Child: `child@mindbridge.test`
- Parent: `parent@mindbridge.test`
- Teacher: `teacher@mindbridge.test`
- Counsellor: `counsellor@mindbridge.test`

## Replace the sample video

Replace:

```text
static/videos/viiii.mp4
```

with your own video, keeping the same filename.

## GitHub

```bash
git init
git add .
git commit -m "Complete MindBridge PostgreSQL prototype"
git branch -M main
git remote add origin https://github.com/YOUR-USERNAME/MindBridge.git
git push -u origin main
```

Never upload `.env`; it is already listed in `.gitignore`.

## Important production note

This is a strong academic prototype. In a real deployment, staff roles such
as teacher and counsellor should be approved by an administrator instead of
being freely selectable during signup.

## Old-design version

This copy uses the colours, cards and page layout from the original `HTML basic`
prototype while keeping the FastAPI and PostgreSQL backend. The original video,
booklet and images are stored under `static/`.
