include uwsgi_params;
uwsgi_param Host $host;
uwsgi_param X-Real-IP $remote_addr;
uwsgi_param X-Forwarded-For $proxy_add_x_forwarded_for;
uwsgi_param X-Forwarded-Proto $scheme;
uwsgi_read_timeout 300s;
uwsgi_connect_timeout 60s;
uwsgi_send_timeout 60s;
uwsgi_pass service:8000;
