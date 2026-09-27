FROM python:3.10

WORKDIR /opt/app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UWSGI_PROCESSES=1 \
    UWSGI_THREADS=16 \
    UWSGI_HARAKIRI=240 \
    DJANGO_SETTINGS_MODULE=example.settings
    
RUN groupadd -r web && useradd -r -g web web

COPY requirements.txt requirements.txt

RUN  pip install --no-cache-dir  --upgrade pip==24.0 \
     && pip install --no-cache-dir -r requirements.txt
     
COPY --chown=web:web . .

RUN  mkdir -p /var/www/static /var/www/media static media /var/log/uwsgi \
    && chown -R web:web /var/www/static /var/www/media /var/log/uwsgi \
    && chmod +x run_uwsgi.sh
    
COPY --chown=web:web uwsgi/uwsgi.ini uwsgi.ini

USER web
EXPOSE 8000

ENTRYPOINT ["./run_uwsgi.sh"]
