FROM python:3.12
LABEL authors="jcivitelli"

WORKDIR /app

COPY __init__.py /app/
COPY celery_app.py /app/
COPY main.py /app/
COPY requirements.txt /app/

RUN pip install -r requirements.txt

CMD ["celery", "-A", "main", "worker", "--beat", "--loglevel=info"]