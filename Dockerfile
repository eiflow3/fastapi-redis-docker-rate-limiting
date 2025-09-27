# 🐍 Use slim Python 3.12 base image
FROM python:3.12-slim

# 🏗️ Set working directory
WORKDIR /app

# install dependencies
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY . /app

# Run uvicorn (use Gunicorn+UvicornWorker in production if you want multiple workers)
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]  