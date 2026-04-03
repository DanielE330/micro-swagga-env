using Microsoft.AspNetCore.Builder;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.AspNetCore.Http;
using Microsoft.OpenApi.Models;
using Npgsql;
using System;
using System.Collections.Generic;
using System.Threading.Tasks;

var builder = WebApplication.CreateBuilder(args);
builder.Services.AddEndpointsApiExplorer();
builder.Services.AddSwaggerGen(c =>
{
    c.SwaggerDoc("v1", new OpenApiInfo
    {
        Title = "Shipping Service",
        Version = "1.0.0",
        Description = "Отслеживание доставки (ASP.NET Core)"
    });
});

var connStr = $"Host={Environment.GetEnvironmentVariable("DB_HOST") ?? "db"};" +
              $"Port={Environment.GetEnvironmentVariable("DB_PORT") ?? "5432"};" +
              $"Database={Environment.GetEnvironmentVariable("DB_NAME") ?? "app_db"};" +
              $"Username={Environment.GetEnvironmentVariable("DB_USER") ?? "postgres"};" +
              $"Password={Environment.GetEnvironmentVariable("DB_PASSWORD") ?? "postgres"}";

var app = builder.Build();

// Init DB
using (var conn = new NpgsqlConnection(connStr))
{
    conn.Open();
    using var cmd = conn.CreateCommand();
    cmd.CommandText = @"
        CREATE TABLE IF NOT EXISTS shipments (
            id SERIAL PRIMARY KEY,
            order_id INTEGER NOT NULL,
            status VARCHAR(50) DEFAULT 'preparing',
            address TEXT NOT NULL,
            tracking_number VARCHAR(100),
            created_at TIMESTAMPTZ DEFAULT NOW()
        )";
    cmd.ExecuteNonQuery();
}

app.UseSwagger();
app.UseSwaggerUI();

app.MapGet("/shipments", async () =>
{
    var rows = new List<Dictionary<string, object>>();
    await using var conn = new NpgsqlConnection(connStr);
    await conn.OpenAsync();
    await using var cmd = new NpgsqlCommand("SELECT * FROM shipments ORDER BY created_at DESC", conn);
    await using var reader = await cmd.ExecuteReaderAsync();
    while (await reader.ReadAsync())
    {
        var row = new Dictionary<string, object>();
        for (int i = 0; i < reader.FieldCount; i++)
            row[reader.GetName(i)] = reader.IsDBNull(i) ? null : reader.GetValue(i);
        rows.Add(row);
    }
    return Results.Ok(rows);
})
.WithName("GetShipments")
.WithTags("Shipments")
.WithOpenApi(op => { op.Summary = "Список всех отправлений"; return op; });

app.MapGet("/shipments/{id}", async (int id) =>
{
    await using var conn = new NpgsqlConnection(connStr);
    await conn.OpenAsync();
    await using var cmd = new NpgsqlCommand("SELECT * FROM shipments WHERE id = @id", conn);
    cmd.Parameters.AddWithValue("id", id);
    await using var reader = await cmd.ExecuteReaderAsync();
    if (!await reader.ReadAsync()) return Results.NotFound(new { error = "Отправление не найдено" });
    var row = new Dictionary<string, object>();
    for (int i = 0; i < reader.FieldCount; i++)
        row[reader.GetName(i)] = reader.IsDBNull(i) ? null : reader.GetValue(i);
    return Results.Ok(row);
})
.WithName("GetShipmentById")
.WithTags("Shipments")
.WithOpenApi(op => { op.Summary = "Получить отправление по ID"; return op; });

app.MapPost("/shipments", async (HttpContext ctx) =>
{
    var body = await ctx.Request.ReadFromJsonAsync<Dictionary<string, object>>();
    var orderId = Convert.ToInt32(body["order_id"]);
    var address = body["address"]?.ToString();
    var tracking = body.ContainsKey("tracking_number") ? body["tracking_number"]?.ToString() : null;

    await using var conn = new NpgsqlConnection(connStr);
    await conn.OpenAsync();
    await using var cmd = new NpgsqlCommand(
        "INSERT INTO shipments (order_id, address, tracking_number) VALUES (@o, @a, @t) RETURNING id", conn);
    cmd.Parameters.AddWithValue("o", orderId);
    cmd.Parameters.AddWithValue("a", address ?? "");
    cmd.Parameters.AddWithValue("t", (object)tracking ?? DBNull.Value);
    var newId = await cmd.ExecuteScalarAsync();
    return Results.Created($"/shipments/{newId}", new { id = newId, order_id = orderId, address, tracking_number = tracking });
})
.WithName("CreateShipment")
.WithTags("Shipments")
.WithOpenApi(op => { op.Summary = "Создать отправление"; return op; });

app.Run("http://0.0.0.0:5000");
