FROM python:3.10

WORKDIR /opt/app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1
    
RUN groupadd -r web && useradd -r -g web web

COPY requirements.txt requirements.txt

RUN  pip install --no-cache-dir  --upgrade pip==24.0 \
     && pip install --no-cache-dir -r requirements.txt
     
RUN mkdir -p /opt/app/log && mkdir -p /opt/app/state && chown -R web:web /opt/app

COPY requirements.txt requirements.txt
     
COPY --chown=web:web . .

USER web

CMD ["python", "main.py"]
