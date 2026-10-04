FROM python:3.12

WORKDIR /opt/app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN groupadd -r web && useradd -r -g web web

COPY requirements.txt requirements.txt

RUN pip install --no-cache-dir --upgrade pip==24.0 \
    && pip install --no-cache-dir -r requirements.txt

RUN mkdir -p /opt/app/src/logs && chown -R web:web /opt/app

COPY --chown=web:web . .

USER web

WORKDIR /opt/app/src

CMD ["fastapi", "run", "main.py", "--host", "0.0.0.0", "--port", "8001"]
