# 🐣 OnboAArrrd

An onboarding platform designed to help new employees integrate smoothly into a company, built with **Django**, **PostgreSQL**, and **Docker**.  

---
## Setup
### 1. Clone the repository
```bash
git clone https://devtools.wi.pb.edu.pl/bitbucket/scm/th2025gr1/onboaarrrd.git
cd OnboAArrrd
```
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
