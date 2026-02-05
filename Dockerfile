FROM python:3.11-slim

# Instalacja bibliotek systemowych wymaganych przez Pillow
RUN apt-get update && apt-get install -y \
    libjpeg-dev \
    zlib1g-dev \
    libpng-dev

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["gunicorn", "-k", "uvicorn.workers.UvicornWorker", "OnboAArrrd.asgi:application", "--bind", "0.0.0.0:8000"]
