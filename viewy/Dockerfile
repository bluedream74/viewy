# Use an official Python runtime as a parent image
FROM python:3.9

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV DJANGO_SETTINGS_MODULE=viewy.settings.production

# Install system dependencies
RUN apt-get update && \
    apt-get install -y ffmpeg pkg-config libmariadb-dev-compat && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Set work directory in the container
WORKDIR /viewy

# Install Python dependencies
COPY requirements.txt /viewy/
RUN pip install -r requirements.txt

# Copy the current directory contents into the container
COPY . /viewy/

CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]