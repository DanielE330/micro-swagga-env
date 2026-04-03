from flask import Flask, request
from flask_restx import Api, Resource, fields
import psycopg2
import psycopg2.extras
import os

app = Flask(__name__)
api = Api(app, title="Notifications Service", version="1.0",
          description="Управление уведомлениями (Flask-RESTX)")

ns = api.namespace("notifications", description="Уведомления")

notification_model = api.model("Notification", {
    "user_id": fields.Integer(required=True, example=1),
    "message": fields.String(required=True, example="Ваш заказ отправлен"),
    "channel": fields.String(default="email", example="email"),
})


def get_conn():
    return psycopg2.connect(
        host=os.getenv("DB_HOST", "db"),
        port=int(os.getenv("DB_PORT", "5432")),
        dbname=os.getenv("DB_NAME", "app_db"),
        user=os.getenv("DB_USER", "postgres"),
        password=os.getenv("DB_PASSWORD", "postgres"),
    )


def init_db():
    conn = get_conn()
    with conn.cursor() as cur:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS notifications (
                id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL,
                message TEXT NOT NULL,
                channel VARCHAR(50) DEFAULT 'email',
                is_read BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMPTZ DEFAULT NOW()
            )
        """)
    conn.commit()
    conn.close()


@ns.route("/")
class NotificationList(Resource):
    def get(self):
        """Список всех уведомлений"""
        conn = get_conn()
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute("SELECT * FROM notifications ORDER BY created_at DESC")
            rows = cur.fetchall()
        conn.close()
        return [dict(r) for r in rows]

    @ns.expect(notification_model)
    def post(self):
        """Создать уведомление"""
        data = request.json
        conn = get_conn()
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(
                "INSERT INTO notifications (user_id, message, channel) VALUES (%s, %s, %s) RETURNING *",
                (data["user_id"], data["message"], data.get("channel", "email")),
            )
            row = cur.fetchone()
        conn.commit()
        conn.close()
        return dict(row), 201


@ns.route("/<int:id>/read")
class MarkRead(Resource):
    def patch(self, id):
        """Отметить уведомление как прочитанное"""
        conn = get_conn()
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(
                "UPDATE notifications SET is_read = TRUE WHERE id = %s RETURNING *",
                (id,),
            )
            row = cur.fetchone()
        conn.commit()
        conn.close()
        if not row:
            api.abort(404, "Уведомление не найдено")
        return dict(row)


if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=8003)
