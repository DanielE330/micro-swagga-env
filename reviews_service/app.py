import os
import sys
import django
from django.conf import settings

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

if not settings.configured:
    settings.configure(
        DEBUG=False,
        SECRET_KEY="django-insecure-test-key-not-for-production",
        ALLOWED_HOSTS=["*"],
        INSTALLED_APPS=[
            "django.contrib.contenttypes",
            "rest_framework",
            "drf_spectacular",
        ],
        DATABASES={
            "default": {
                "ENGINE": "django.db.backends.postgresql",
                "HOST": os.getenv("DB_HOST", "db"),
                "PORT": os.getenv("DB_PORT", "5432"),
                "NAME": os.getenv("DB_NAME", "app_db"),
                "USER": os.getenv("DB_USER", "postgres"),
                "PASSWORD": os.getenv("DB_PASSWORD", "postgres"),
            }
        },
        ROOT_URLCONF="app",
        DEFAULT_AUTO_FIELD="django.db.models.BigAutoField",
        REST_FRAMEWORK={
            "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
        },
        SPECTACULAR_SETTINGS={
            "TITLE": "Reviews Service",
            "DESCRIPTION": "Отзывы на товары (Django REST Framework)",
            "VERSION": "1.0.0",
            "SERVE_INCLUDE_SCHEMA": False,
        },
    )
    django.setup()

from django.db import models, connection


class Review(models.Model):
    product_id = models.IntegerField()
    user_id = models.IntegerField()
    rating = models.IntegerField()
    text = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = "reviews"
        db_table = "reviews"


def ensure_table():
    with connection.cursor() as cur:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS reviews (
                id SERIAL PRIMARY KEY,
                product_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                rating INTEGER NOT NULL,
                text TEXT DEFAULT '',
                created_at TIMESTAMPTZ DEFAULT NOW()
            )
        """)


from rest_framework import serializers, viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response


class ReviewSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    product_id = serializers.IntegerField()
    user_id = serializers.IntegerField()
    rating = serializers.IntegerField(min_value=1, max_value=5)
    text = serializers.CharField(required=False, default="")
    created_at = serializers.DateTimeField(read_only=True)


class ReviewViewSet(viewsets.ViewSet):
    serializer_class = ReviewSerializer

    def list(self, request):
        """Список всех отзывов"""
        with connection.cursor() as cur:
            cur.execute("SELECT id, product_id, user_id, rating, text, created_at FROM reviews ORDER BY created_at DESC")
            cols = [c.name for c in cur.description]
            rows = [dict(zip(cols, r)) for r in cur.fetchall()]
        return Response(rows)

    def create(self, request):
        """Создать отзыв"""
        s = ReviewSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        d = s.validated_data
        with connection.cursor() as cur:
            cur.execute(
                "INSERT INTO reviews (product_id, user_id, rating, text) VALUES (%s,%s,%s,%s) RETURNING id, product_id, user_id, rating, text, created_at",
                [d["product_id"], d["user_id"], d["rating"], d.get("text", "")],
            )
            cols = [c.name for c in cur.description]
            row = dict(zip(cols, cur.fetchone()))
        return Response(row, status=status.HTTP_201_CREATED)

    def retrieve(self, request, pk=None):
        """Получить отзыв по ID"""
        with connection.cursor() as cur:
            cur.execute("SELECT id, product_id, user_id, rating, text, created_at FROM reviews WHERE id = %s", [pk])
            if cur.rowcount == 0:
                return Response({"error": "Отзыв не найден"}, status=status.HTTP_404_NOT_FOUND)
            cols = [c.name for c in cur.description]
            row = dict(zip(cols, cur.fetchone()))
        return Response(row)


from django.urls import path, include
from rest_framework.routers import DefaultRouter
from drf_spectacular.views import SpectacularAPIView

router = DefaultRouter()
router.register(r"reviews", ReviewViewSet, basename="review")

urlpatterns = [
    path("", include(router.urls)),
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
]


if __name__ == "__main__":
    ensure_table()
    from django.core.management import execute_from_command_line
    execute_from_command_line(["manage", "runserver", "0.0.0.0:8004"])
