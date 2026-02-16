FROM python:3.10-slim

WORKDIR /app

# ffmpeg install (stream recording ke liye)
RUN apt-get update && apt-get install -y ffmpeg \
    && apt-get clean

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "bot.py"]
