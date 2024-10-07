FROM python:3.8.10-slim-bullseye

ENV PIP_DEFAULT_TIMEOUT=100 \
    #* Allow statements and log messages to immediately appear
    PYTHONUNBUFFERED=1

# RUN apt-get update && apt-get upgrade -y

COPY requirements.txt .
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

COPY . .

WORKDIR /sedr

EXPOSE 8000

#* Start the Django server
CMD ["runserver", "0.0.0.0:8000"]
