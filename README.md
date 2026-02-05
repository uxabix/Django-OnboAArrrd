# 🐣 OnboAArrrd

An onboarding platform designed to help new employees integrate smoothly into a company, built with **Django**, **PostgreSQL**, and **Docker**.  

--- 

## 🐘 Troubleshooting: Migrations Not Applying

If your migrations fail to apply or you encounter inconsistent migration history, you may need to reset the PostgreSQL database completely.
To do this, remove the entire Postgres Docker volume (⚠️ this will delete all database data 🙂):
```bash
docker compose down -v
docker compose up -d
```
After bringing the containers back up, re-run your migrations:
```bash
docker compose exec web python manage.py migrate
```
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

# Database Seeding Guide

This project provides modular seeding scripts for populating the database with test data. The seeds cover both `accounts` and `onboarding` applications and can be run individually or all together. The scripts are designed to be configurable by the number of records to create.

---

## 1. General Usage

All seed commands are implemented as Django management commands under `core/management/commands/seed.py`. You can run the seeders with:

python manage.py seed <seeder_name> [--count <number>]

- `<seeder_name>`: The name of the seeder module to run (see the list below).  
- `--count <number>`: Optional parameter to control how many records to create. Default is `10`.

To run multiple seeders sequentially:

`python manage.py seed roles users badges competency_paths tasks quizzes user_paths user_tasks task_status reports user_grades messages --count 10`

---

## 2. Seeders

### **Accounts Application**

- `roles` – creates roles in the system (e.g., Mentor, Student).  
- `users` – creates test users, assigns them to the `TestUsers` group, and links students to mentors.  

### **Onboarding Application**

- `badges` – creates badges.  
- `competency_paths` – creates competency paths.  
- `task_types` – creates task types (text, quiz, etc.).  
- `tasks` – creates tasks for competency paths.  
- `quizzes` – creates quizzes, questions, and answers linked to tasks.  
- `user_paths` – assigns competency paths to users.  
- `user_tasks` – assigns tasks to users with deadlines and `assigned_by` references.  
- `task_status` – creates multiple statuses for each user task.  
- `reports` – generates reports between users.  
- `user_grades` – assigns grades to completed tasks.

### **Chat Application**

- `messages` – creates messages between the user and his mentor in the system.

---

## 3. Examples

Run all seeders:
```bash
docker compose exec web python manage.py seed 
```
Create 10 roles:
```bash
docker compose exec web python manage.py seed roles --count 10
```
Create 50 users and assign them to the `TestUsers` group:
```bash
docker compose exec web python manage.py seed users --count 50
```
Create tasks and related quizzes:
```bash
docker compose exec web python manage.py seed tasks quizzes --count 100
```
Generate user paths, tasks, and task statuses:
```bash
docker compose exec web python manage.py seed user_paths user_tasks task_status --count 5
```
Generate reports and grades:
```bash
docker compose exec web python manage.py seed reports user_grades --count 20
```
---
### Clearing Test Data

You can remove all data related to users in the `TestUsers` group using the `clear_test_data` management command. This is useful if you want to reset the test data without affecting real users.

Run the command:
```bash
docker compose exec web python manage.py clear_test_data
```

This will delete:

- All `CustomUser` instances in the `TestUsers` group  
- Related onboarding data, including:
  - `User_badges`
  - `User_paths`
  - `User_tasks`
  - `Task_status`
  - `Reports`
  - `User_grade`

The command uses a database transaction to ensure all related data is removed safely.

---

## 4. Notes

- Seeders are **modular**: you can run each one independently in any order, but some depend on others. For example:  
  - `users` depends on `roles`.  
  - `tasks` depends on `competency_paths` and `task_types`.  
  - `quizzes` depend on `tasks`.  
  - `user_tasks` depends on `users` and `tasks`.  
- All seeds are **deterministic** (no Faker) and produce repeatable results.
- You can modify the `--count` argument to generate more or fewer records depending on your testing needs.  

---

## 5. Summary

Seeding scripts allow you to quickly populate the database with realistic test data across all models in `accounts` and `onboarding`. Use the modular commands or run them all sequentially for a full setup.

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
