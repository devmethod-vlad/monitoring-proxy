# edu-monitoring-proxy

## Утилита tree.py
### Рисует дерево проекта в терминале


```
python app/utils/tree.py .
```

### Для тестирования с проектами из https://git.emias.mos.ru/emias.education.development/monitoring-proxy-concept

```
docker network create observability

```

### При создании алерта в графане всегда необходимо указывать custom annotation 'query_match' и внутри - запрос LogQL, к примеру {job="testapp"} |= "ERROR"

## В корне проекта создать .env файл, туда скопировать


```
COMPOSE_PATH_SEPARATOR=;
COMPOSE_FILE=docker-compose.yml;docker-compose.dev.yml


APP_TITLE=edu-alert-proxy
APP_MODE=dev
APP_HOST=0.0.0.0
APP_PORT=8004
APP_DEBUG=true
APP_ROOT_PATH=/alert-proxy


EMAIL_SMTP_SERVER=
EMAIL_SMTP_PORT=
EMAIL_SMTP_HELO=
EMAIL_SMTP_USERNAME=
EMAIL_SMTP_PASSWORD=


REDIS_DSN=redis://alert-proxy-redis:6379
REDIS_PORT=6379



ALERT_CONTEXT_BEFORE=2
ALERT_CONTEXT_AFTER=2
ALERT_CONTEXT_TIME_RANGE=30m
ALERT_SEARCH_WINDOW=5m
ALERT_MAX_MATCHES=3
ALERT_DEFAULT_QUERY_MATCH='{job="testapp"} |= "ERROR"'
LOKI_BASE_URL=http://loki-proxy:3100
LOKI_TIMEOUT_S=15

TELEGRAM_BOT_TOKEN= # токен бота
TELEGRAM_PARSE_MODE=HTML
TELEGRAM_MAX_CHARS=3500

TEMPLATE_DIR=app/templates
TEMPLATE_TG=telegram_default.j2
TEMPLATE_EMAIL=email_default.j2

RECEIVERS_TG_IDS= # тг id получателей через запятую
RECEIVERS_EMAILS= # email получателей через запятую


AVAILABLE_CHANNELS=telegram,email


LOG_APP_DIR=./logs/app
LOG_APP_LOG_FILE=app.log
LOG_CELERY_DIR=./logs/celery
LOG_CELERY_LOG_FILE=celery.log


# Если хотим невычисляемое число воркеров celery и granian

SCALE_BACKEND_WORKERS=4
SCALE_CELERY_WORKERS=4

```
