# Use an official Python runtime as a parent image
FROM python:3.9

# Set environment varibles
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set work directory in the container to /helloproject
WORKDIR /viewy

# Install dependencies
COPY requirements.txt /viewy/
RUN pip install -r requirements.txt

# Copy the current directory contents (i.e., your Django app) into the container at /helloproject
COPY . /viewy/

CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]