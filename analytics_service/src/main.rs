use axum::{
    extract::{Path, State},
    http::StatusCode,
    response::Json,
    routing::{get, post},
    Router,
};
use serde::{Deserialize, Serialize};
use serde_json::{json, Value};
use std::sync::Arc;
use tokio_postgres::{Client, NoTls};
use utoipa::{OpenApi, ToSchema};

#[derive(Serialize, ToSchema)]
struct Event {
    id: i32,
    event_type: String,
    payload: String,
    created_at: String,
}

#[derive(Deserialize, ToSchema)]
struct CreateEvent {
    event_type: String,
    payload: Option<String>,
}

type Db = Arc<Client>;

#[utoipa::path(get, path = "/events", tag = "Analytics",
    responses((status = 200, description = "Список событий")))]
async fn list_events(State(db): State<Db>) -> Json<Value> {
    let rows = db.query("SELECT id, event_type, payload, created_at::text FROM events ORDER BY created_at DESC", &[]).await.unwrap();
    let events: Vec<Value> = rows.iter().map(|r| {
        json!({ "id": r.get::<_, i32>(0), "event_type": r.get::<_, String>(1),
                 "payload": r.get::<_, String>(2), "created_at": r.get::<_, String>(3) })
    }).collect();
    Json(json!(events))
}

#[utoipa::path(get, path = "/events/{id}", tag = "Analytics",
    params(("id" = i32, Path, description = "ID события")),
    responses((status = 200, description = "Событие"), (status = 404, description = "Не найдено")))]
async fn get_event(State(db): State<Db>, Path(id): Path<i32>) -> Result<Json<Value>, StatusCode> {
    let rows = db.query("SELECT id, event_type, payload, created_at::text FROM events WHERE id = $1", &[&id]).await.unwrap();
    if rows.is_empty() {
        return Err(StatusCode::NOT_FOUND);
    }
    let r = &rows[0];
    Ok(Json(json!({ "id": r.get::<_, i32>(0), "event_type": r.get::<_, String>(1),
                     "payload": r.get::<_, String>(2), "created_at": r.get::<_, String>(3) })))
}

#[utoipa::path(post, path = "/events", tag = "Analytics",
    request_body = CreateEvent,
    responses((status = 201, description = "Создано")))]
async fn create_event(State(db): State<Db>, Json(body): Json<CreateEvent>) -> (StatusCode, Json<Value>) {
    let payload = body.payload.unwrap_or_default();
    let row = db.query_one(
        "INSERT INTO events (event_type, payload) VALUES ($1, $2) RETURNING id, event_type, payload, created_at::text",
        &[&body.event_type, &payload],
    ).await.unwrap();
    (StatusCode::CREATED, Json(json!({
        "id": row.get::<_, i32>(0), "event_type": row.get::<_, String>(1),
        "payload": row.get::<_, String>(2), "created_at": row.get::<_, String>(3)
    })))
}

#[derive(OpenApi)]
#[openapi(
    info(title = "Analytics Service", version = "1.0.0", description = "Аналитика событий (Rust / Axum)"),
    paths(list_events, get_event, create_event),
    components(schemas(Event, CreateEvent))
)]
struct ApiDoc;

#[tokio::main]
async fn main() {
    let host = std::env::var("DB_HOST").unwrap_or_else(|_| "db".into());
    let port = std::env::var("DB_PORT").unwrap_or_else(|_| "5432".into());
    let dbname = std::env::var("DB_NAME").unwrap_or_else(|_| "app_db".into());
    let user = std::env::var("DB_USER").unwrap_or_else(|_| "postgres".into());
    let pass = std::env::var("DB_PASSWORD").unwrap_or_else(|_| "postgres".into());

    let conn_str = format!("host={host} port={port} dbname={dbname} user={user} password={pass}");
    let (client, connection) = tokio_postgres::connect(&conn_str, NoTls).await.unwrap();
    tokio::spawn(async move { if let Err(e) = connection.await { eprintln!("DB error: {e}"); } });

    client.execute(
        "CREATE TABLE IF NOT EXISTS events (
            id SERIAL PRIMARY KEY,
            event_type VARCHAR(100) NOT NULL,
            payload TEXT DEFAULT '',
            created_at TIMESTAMPTZ DEFAULT NOW()
        )", &[],
    ).await.unwrap();

    let db: Db = Arc::new(client);

    let spec = ApiDoc::openapi().to_pretty_json().unwrap();
    let spec_clone = spec.clone();

    let app = Router::new()
        .route("/events", get(list_events).post(create_event))
        .route("/events/{id}", get(get_event))
        .route("/api-doc/openapi.json", get(move || async move { Json(serde_json::from_str::<Value>(&spec_clone).unwrap()) }))
        .with_state(db);

    let listener = tokio::net::TcpListener::bind("0.0.0.0:8088").await.unwrap();
    println!("[analytics_service] listening on 8088");
    axum::serve(listener, app).await.unwrap();
}
