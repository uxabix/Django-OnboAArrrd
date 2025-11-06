# 🐣 OnboAArrrd

An onboarding platform designed to help new employees integrate smoothly into a company, built with **Django**, **PostgreSQL**, and **Docker**.  

---
## Setup
### 1. Clone the repository
```bash
git clone https://devtools.wi.pb.edu.pl/bitbucket/scm/th2025gr1/onboaarrrd.git
cd OnboAArrrd
```
### 1.5. Gitconfig
If you want to automatically push to both **Bitbucket** and **GitHub**,  
you need to update your local `.git/config` file.

#### 1. Add GitHub as an additional push target
You can either edit `.git/config` manually or use the command line.

Option A – Command line
```bash
git remote set-url --add --push origin https://devtools.wi.pb.edu.pl/bitbucket/scm/th2025gr1/onboaarrrd.git
git remote set-url --add --push origin https://github.com/uxabix/Django-OnboAArrrd.git
```

Option B – Manual edit
Open `.git/config` and make sure the `[remote "origin"]` section looks like this:
```ini
[remote "origin"]
    url = https://bitbucket.org/your-university/onboaarrd.git
    fetch = +refs/heads/*:refs/remotes/origin/*
    pushurl = https://devtools.wi.pb.edu.pl/bitbucket/scm/th2025gr1/onboaarrrd.git
    pushurl = https://github.com/uxabix/Django-OnboAArrrd.git
```

#### 2. Verify
Run:
```bash
git remote show origin
```
You should see **two Push URLs** — one for Bitbucket and one for GitHub.

Now, every time you push:
```bash
git push --all
```
Git will automatically send all branches and commits to **both repositories** 🎯


### 2. Configure environment variables
Copy .env.example to .env:
```bash
cp .env.example .env
```
### 3. Start the project
Run containers:
```bash
docker compose up --build
```
Available services:
- Django + Channels: http://localhost:8000
- Admin panel: http://localhost:8000/admin
- PostgreSQL: http://localhost:5050/

### 4. Apply migrations and create a superuser
Run migrations:
```bash
docker compose exec web python manage.py makemigrations
docker compose exec web python manage.py migrate
```
Create a superuser:
```bash
docker compose exec web python manage.py createsuperuser
```

### 5. Generate static files
```bash
docker compose exec web python manage.py collectstatic
```

### 6. Work with Django
All commands should be executed inside the web container. Examples:
```bash
docker compose exec web python manage.py shell
docker compose exec web python manage.py makemigrations
docker compose exec web pytest -v 
```

### 7. Stop containers
```bash
docker compose down
```
---

## 🚀 Stack
- Django, Channels  
- PostgreSQL  
- Docker  
- GitFlow  
- Sphinx  

---

## 📌 Status
Early development stage.  
See [ROADMAP.md](./ROADMAP.md) for the roadmap.  

---

## ⚖️ License
No license yet. **All rights reserved by the authors.**
