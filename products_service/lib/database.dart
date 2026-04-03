import 'dart:io';
import 'package:postgres/postgres.dart';

Connection? _db;

/// Возвращает активное соединение с БД (ленивая инициализация).
Future<Connection> getDatabase() async {
  if (_db != null) return _db!;

  _db = await Connection.open(
    Endpoint(
      host: Platform.environment['DB_HOST'] ?? 'db',
      port: int.tryParse(Platform.environment['DB_PORT'] ?? '') ?? 5432,
      database: Platform.environment['DB_NAME'] ?? 'app_db',
      username: Platform.environment['DB_USER'] ?? 'postgres',
      password: Platform.environment['DB_PASSWORD'] ?? 'postgres',
    ),
    settings: const ConnectionSettings(sslMode: SslMode.disable),
  );

  await _db!.execute('''
    CREATE TABLE IF NOT EXISTS products (
      id          SERIAL PRIMARY KEY,
      name        TEXT NOT NULL,
      description TEXT,
      price       FLOAT8 NOT NULL DEFAULT 0,
      stock       INTEGER NOT NULL DEFAULT 0,
      created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
    )
  ''');

  return _db!;
}

/// Конвертирует строку результата в JSON-совместимый Map.
Map<String, dynamic> rowToMap(Map<String, dynamic> row) {
  return row.map((key, value) {
    if (value is DateTime) return MapEntry(key, value.toIso8601String());
    return MapEntry(key, value);
  });
}
