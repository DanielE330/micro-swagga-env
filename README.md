# Microservices Playground

Учебный проект — коллекция микросервисов на разных технологиях, объединённых единым API-шлюзом и автоматической документацией.

## Стек

| Слой | Технология |
|------|-----------|
| Reverse-proxy / шлюз | [Caddy 2](https://caddyserver.com/) |
| База данных | PostgreSQL 15 |
| Документация | `docs_service` (FastAPI + Swagger UI) |
| Оркестрация | Docker Compose |

### Микросервисы

| Сервис | Язык | Фреймворк | Путь |
|--------|------|-----------|------|
| auth_service | Python | FastAPI | `/auth` |
| user_service | Python | FastAPI | `/users` |
| notifications_service | Python | Flask-RESTX | `/notifications` |
| reviews_service | Python | Django REST Framework | `/reviews` |
| categories_service | TypeScript | NestJS | `/categories` |
| tags_service | JavaScript | Hapi | `/tags` |
| orders_service | JavaScript | Express | `/orders` |
| products_service | Dart | Dart Frog | `/products` |
| inventory_service | Java | Spring Boot | `/inventory` |
| shipping_service | C# | ASP.NET Core | `/shipping` |
| payments_service | Go | Gin | `/payments` |
| comments_service | Ruby | Grape | `/comments` |
| coupons_service | PHP | Slim | `/coupons` |
| analytics_service | Rust | Axum + utoipa | `/analytics` |

---

## Быстрый старт

```bash
cd backend
docker compose up --build
```

- API-шлюз: **http://localhost:8080**
- Документация всех сервисов: **http://localhost:8080/docs**

---

## docs_service

`docs_service` — это агрегатор документации. Он не требует ручной настройки при добавлении нового сервиса: всё работает автоматически через Docker labels.

### Как это работает

1. `docs_service` подключается к Docker-сокету (`/var/run/docker.sock`) и опрашивает список запущенных контейнеров через Docker API.
2. Из всех контейнеров того же Compose-проекта отбираются те, у которых есть label `docs.route`.
3. Для каждого такого сервиса `docs_service` пытается найти OpenAPI-спеку, перебирая десятки стандартных путей (`/openapi.json`, `/v3/api-docs`, `/swagger/doc.json`, и т.д.).  
   Если нужен нестандартный путь — укажите label `docs.openapi=/your/path`.
4. Найденные спеки кешируются на `CACHE_TTL` секунд (по умолчанию 30).
5. На странице `/docs` рендерится Swagger UI со всеми обнаруженными сервисами в виде вкладок.

### Labels для подключения сервиса

```yaml
labels:
  - "docs.route=/prefix"       # обязательно — путь в Caddy
  - "docs.port=8080"           # рекомендуется — внутренний порт сервиса
  - "docs.openapi=/path"       # опционально — если стандартные пути не подходят
```

### Переменные окружения docs_service

| Переменная | По умолчанию | Описание |
|------------|-------------|----------|
| `CACHE_TTL` | `30` | Время кеширования списка сервисов (секунды) |
| `COMPOSE_SERVICE` | `docs_service` | Имя собственного контейнера в Compose |

---

## Добавление нового микросервиса

### Шаг 1. Создайте директорию сервиса

```
backend/
  my_service/
    Dockerfile
    ...
```

### Шаг 2. Добавьте сервис в `docker-compose.yml`

```yaml
my_service:
  build: ./my_service
  labels:
    - "docs.route=/my"
    - "docs.port=8099"
  expose:
    - "8099"
  environment:
    - DB_HOST=db
    - DB_PORT=5432
    - DB_NAME=app_db
    - DB_USER=postgres
    - DB_PASSWORD=postgres
  depends_on:
    db:
      condition: service_healthy
```

### Шаг 3. Добавьте маршрут в `Caddyfile`

```caddy
route /my/* {
    uri strip_prefix /my
    reverse_proxy my_service:8099
}
```

### Шаг 4. Добавьте сервис в `depends_on` Caddy

```yaml
caddy:
  depends_on:
    - my_service   # ← добавить
```

`docs_service` подхватит сервис автоматически по label.

---

## Инструкции по фреймворкам

### Python — FastAPI

FastAPI публикует спеку на `/openapi.json` автоматически.

```python
from fastapi import FastAPI
app = FastAPI(title="My Service")

@app.get("/items")
def get_items():
    return []
```

`Dockerfile`:
```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8099
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8099"]
```

`requirements.txt`: `fastapi`, `uvicorn`

---

### Python — Flask-RESTX

Flask-RESTX публикует спеку на `/swagger.json`.

```python
from flask import Flask
from flask_restx import Api, Resource

app = Flask(__name__)
api = Api(app, title="My Service")

ns = api.namespace("items")

@ns.route("/")
class Items(Resource):
    def get(self):
        return []
```

`Dockerfile`:
```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8099
CMD ["python", "app.py"]
```

`requirements.txt`: `flask`, `flask-restx`

---

### Python — Django REST Framework

DRF со `drf-spectacular` публикует спеку на `/api/schema/`.

```python
# settings.py
INSTALLED_APPS = [..., "rest_framework", "drf_spectacular"]
REST_FRAMEWORK = {"DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema"}

# urls.py
from drf_spectacular.views import SpectacularAPIView
urlpatterns = [
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    ...
]
```

`requirements.txt`: `django`, `djangorestframework`, `drf-spectacular`, `gunicorn`

Label в Compose: `docs.openapi=/api/schema/` (если автоопределение не срабатывает).

---

### TypeScript — NestJS

NestJS со `@nestjs/swagger` публикует спеку на `/api-json`.

```typescript
// main.ts
import { SwaggerModule, DocumentBuilder } from "@nestjs/swagger";

const config = new DocumentBuilder().setTitle("My Service").build();
const document = SwaggerModule.createDocument(app, config);
SwaggerModule.setup("api", app, document);
```

`Dockerfile`:
```dockerfile
FROM node:20-alpine AS build
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build

FROM node:20-alpine
WORKDIR /app
COPY package*.json ./
RUN npm install --omit=dev
COPY --from=build /app/dist ./dist
EXPOSE 3001
CMD ["node", "dist/main"]
```

Пакеты: `@nestjs/swagger`, `swagger-ui-express`

---

### JavaScript — Hapi

Hapi с `@hapi/hapi` + `hapi-swagger` публикует спеку на `/swagger.json`.

```javascript
const Hapi = require("@hapi/hapi");
const HapiSwagger = require("hapi-swagger");
const Inert = require("@hapi/inert");
const Vision = require("@hapi/vision");

const server = Hapi.server({ port: 3002, host: "0.0.0.0" });

await server.register([Inert, Vision, { plugin: HapiSwagger, options: { info: { title: "My Service" } } }]);
```

`Dockerfile`:
```dockerfile
FROM node:20-alpine
WORKDIR /app
COPY package*.json ./
RUN npm install --omit=dev
COPY . .
EXPOSE 3002
CMD ["node", "index.js"]
```

Пакеты: `@hapi/hapi`, `@hapi/inert`, `@hapi/vision`, `hapi-swagger`

---

### JavaScript — Express

Express с `swagger-ui-express` + `swagger-jsdoc` публикует спеку на `/api-docs`.

```javascript
const express = require("express");
const swaggerUi = require("swagger-ui-express");
const swaggerJsdoc = require("swagger-jsdoc");

const app = express();
const spec = swaggerJsdoc({ definition: { openapi: "3.0.0", info: { title: "My Service", version: "1.0.0" } }, apis: ["./routes/*.js"] });
app.use("/api-docs", swaggerUi.serve, swaggerUi.setup(spec));
```

`Dockerfile`:
```dockerfile
FROM node:20-alpine
WORKDIR /app
COPY package*.json ./
RUN npm install --omit=dev
COPY src/ ./src/
EXPOSE 3000
CMD ["node", "src/index.js"]
```

Пакеты: `express`, `swagger-ui-express`, `swagger-jsdoc`

---

### Dart — Dart Frog

Dart Frog публикует спеку на `/openapi.json` при использовании пакета `dart_frog_open_api`.

```dart
// routes/openapi.json.dart
import "package:dart_frog_open_api/dart_frog_open_api.dart";

Response onRequest(RequestContext context) => OpenApiRoute().handler(context);
```

`Dockerfile`:
```dockerfile
FROM dart:stable AS build
WORKDIR /app
RUN dart pub global activate dart_frog_cli
COPY pubspec.yaml ./
RUN dart pub get --no-precompile
COPY . .
RUN dart pub get && dart_frog build
RUN dart compile exe build/bin/server.dart -o build/bin/server

FROM scratch
COPY --from=build /runtime/ /
COPY --from=build /app/build/bin/server /app/bin/server
EXPOSE 8080
CMD ["/app/bin/server"]
```

`pubspec.yaml` зависимости: `dart_frog`, `dart_frog_open_api`

---

### Java — Spring Boot

Spring Boot со `springdoc-openapi` публикует спеку на `/v3/api-docs`.

```xml
<!-- pom.xml -->
<dependency>
    <groupId>org.springdoc</groupId>
    <artifactId>springdoc-openapi-starter-webmvc-ui</artifactId>
    <version>2.x.x</version>
</dependency>
```

`Dockerfile`:
```dockerfile
FROM eclipse-temurin:17-jdk-alpine AS build
WORKDIR /app
COPY pom.xml .
COPY src/ ./src/
RUN apk add --no-cache maven && mvn package -DskipTests -q

FROM eclipse-temurin:17-jre-alpine
WORKDIR /app
COPY --from=build /app/target/*.jar app.jar
EXPOSE 8085
CMD ["java", "-jar", "app.jar"]
```

---

### C# — ASP.NET Core

ASP.NET Core со `Swashbuckle` публикует спеку на `/swagger/v1/swagger.json`.

```csharp
// Program.cs
builder.Services.AddEndpointsApiExplorer();
builder.Services.AddSwaggerGen();
// ...
app.UseSwagger();
app.UseSwaggerUI();
```

`Dockerfile`:
```dockerfile
FROM mcr.microsoft.com/dotnet/sdk:8.0-alpine AS build
WORKDIR /app
COPY *.csproj ./
RUN dotnet restore
COPY . .
RUN dotnet publish -c Release -o out

FROM mcr.microsoft.com/dotnet/aspnet:8.0-alpine
WORKDIR /app
COPY --from=build /app/out .
EXPOSE 5000
CMD ["dotnet", "MyService.dll"]
```

NuGet: `Swashbuckle.AspNetCore`

---

### Go — Gin

Gin со `swag` публикует спеку на `/swagger/doc.json`.

```go
// main.go
import (
    ginSwagger "github.com/swaggo/gin-swagger"
    swaggerFiles "github.com/swaggo/files"
    _ "myservice/docs"
)

r.GET("/swagger/*any", ginSwagger.WrapHandler(swaggerFiles.Handler))
```

Генерация спеки: `swag init` перед сборкой.

`Dockerfile`:
```dockerfile
FROM golang:1.21-alpine AS build
WORKDIR /app
COPY go.mod ./
RUN go mod download
COPY . .
RUN CGO_ENABLED=0 go build -o server .

FROM alpine:3.19
WORKDIR /app
COPY --from=build /app/server .
EXPOSE 8086
CMD ["./server"]
```

---

### Ruby — Grape

Grape с `grape-swagger` публикует спеку на `/api/swagger_doc`.

```ruby
# app.rb
require "grape-swagger"

class API < Grape::API
  add_swagger_documentation(
    api_version: "v1",
    info: { title: "My Service" }
  )
end
```

`Dockerfile`:
```dockerfile
FROM ruby:3.3-slim
RUN apt-get update && apt-get install -y build-essential libpq-dev && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY Gemfile ./
RUN bundle install --without development test
COPY . .
EXPOSE 3003
CMD ["bundle", "exec", "rackup", "--host", "0.0.0.0", "--port", "3003"]
```

Gem'ы: `grape`, `grape-swagger`, `rack`

Label в Compose: `docs.openapi=/api/swagger_doc`

---

### PHP — Slim

Slim с `swagger-php` и `zircote/swagger-php` публикует спеку на `/api/doc.json`.

```php
// public/index.php
$app->get("/api/doc.json", function ($request, $response) {
    $openapi = \OpenApi\Generator::scan(["../src"]);
    $response->getBody()->write($openapi->toJson());
    return $response->withHeader("Content-Type", "application/json");
});
```

`Dockerfile`:
```dockerfile
FROM php:8.3-cli-alpine
RUN apk add --no-cache postgresql-dev curl && docker-php-ext-install pdo pdo_pgsql
RUN curl -sS https://getcomposer.org/installer | php -- --install-dir=/usr/local/bin --filename=composer
WORKDIR /app
COPY composer.json .
RUN composer install --no-dev --no-interaction --optimize-autoloader
COPY . .
EXPOSE 8087
CMD ["php", "-S", "0.0.0.0:8087", "-t", "public", "public/index.php"]
```

Пакеты Composer: `slim/slim`, `zircote/swagger-php`

Label в Compose: `docs.openapi=/api/doc.json`

---

### Rust — Axum + utoipa

utoipa с axum публикует спеку на `/api-doc/openapi.json`.

```rust
use utoipa::OpenApi;
use utoipa_swagger_ui::SwaggerUi;

#[derive(OpenApi)]
#[openapi(paths(get_items))]
struct ApiDoc;

let app = Router::new()
    .merge(SwaggerUi::new("/swagger-ui").url("/api-doc/openapi.json", ApiDoc::openapi()));
```

`Dockerfile`:
```dockerfile
FROM rust:1.86-slim-bookworm AS build
RUN apt-get update && apt-get install -y pkg-config libssl-dev curl && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY Cargo.toml .
RUN mkdir src && echo 'fn main(){}' > src/main.rs && cargo build --release 2>/dev/null; true
COPY src/ ./src/
RUN cargo build --release

FROM debian:bookworm-slim
RUN apt-get update && apt-get install -y libssl3 ca-certificates && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY --from=build /app/target/release/my_service .
EXPOSE 8088
CMD ["./my_service"]
```

Crate'ы: `axum`, `tokio`, `utoipa`, `utoipa-swagger-ui`

> **Важно:** `utoipa-swagger-ui` во время сборки скачивает архив Swagger UI через `curl` — он должен быть установлен в build-образе.
