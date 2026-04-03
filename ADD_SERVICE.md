## 📋 Как добавлять новые микросервисы:

### 1. **Создайте директорию** для сервиса
```
backend/
  new_service/
    main.py
    requirements.txt
    Dockerfile
    models.py
    database.py
    schemas.py
```

### 2. **Добавьте в docker-compose.yml** (выберите свободный порт, например 8003):
```yaml
  new_service:
    build: ./new_service
    expose:
      - "8003"
    environment:
      - DATABASE_URL=postgresql://postgres:postgres@db:5432/app_db
      - SERVICE_NAME=new_service
    env_file:
      - .env
    depends_on:
      db:
        condition: service_healthy
```

### 3. **Обновите Caddyfile** для маршрутизации:
```caddy
    # Маршрут для нового сервиса
    route /new/* {
        uri strip_prefix /new
        reverse_proxy new_service:8003
    }
```

### 4. **Обновите зависимости** в Caddy:
```yaml
  caddy:
    depends_on:
      - auth_service
      - user_service
      - docs_service
      - new_service  # ← добавить сюда
```

### 5. **Обновите docs_service**, добавив сервис в переменную окружения:
```yaml
environment:
  - SERVICES=Auth Service=/auth,User Service=/users,New Service=/new
```

**Порты по схеме:**
- `8000` - docs_service (документация)
- `8001` - user_service
- `8002` - auth_service
- `8003+` - новые сервисы

Все микросервисы общаются из `docker-compose` сети по имени контейнера!

Внесены изменения.