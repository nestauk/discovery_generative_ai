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
COPY app.py /app/app.py

# Don't push the image to dockerhub
COPY .env /app/.env
COPY .streamlit /app/.streamlit

# Project initialization:
RUN poetry config virtualenvs.create false \
    && poetry install --no-interaction --no-ansi



EXPOSE 8501
# Specify the command to run your application
CMD ["sh", "-c", "streamlit run --server.port $PORT app.py"]
