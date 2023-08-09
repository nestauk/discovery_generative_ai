# Use an official Python runtime as a parent image
FROM --platform=linux/amd64 python:3.9.17-slim

# Set environment varibles
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Install system dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends gcc

# Install poetry
RUN pip install "poetry==1.5.1"

# Set the working directory in the Docker image
WORKDIR /app

# Copy only requirements to cache them in docker layer
COPY pyproject.toml poetry.lock ./
COPY src/genai  /app/src/genai
COPY README.md /app/README.md
COPY whatsapp_bot.py /app/whatsapp_bot.py

# Don't push the image to dockerhub
COPY .env /app/.env

# Project initialization:
RUN poetry config virtualenvs.create false \
    && poetry install --no-interaction --no-ansi

# Specify the command to run your application
CMD ["sh", "-c", "gunicorn --bind 0.0.0.0:$PORT whatsapp_bot:app"]
