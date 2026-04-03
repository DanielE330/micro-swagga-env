package main

import (
	"database/sql"
	"encoding/json"
	"fmt"
	"net/http"
	"os"
	"strconv"

	"github.com/gin-gonic/gin"
	_ "github.com/lib/pq"
)

var db *sql.DB

func env(key, def string) string {
	if v := os.Getenv(key); v != "" {
		return v
	}
	return def
}

// OpenAPI спека (Gin swag-совместимый путь /swagger/doc.json)
var openapiSpec = map[string]interface{}{
	"openapi": "3.0.0",
	"info": map[string]interface{}{
		"title":       "Payments Service",
		"version":     "1.0.0",
		"description": "Обработка платежей (Gin / Go)",
	},
	"paths": map[string]interface{}{
		"/payments": map[string]interface{}{
			"get": map[string]interface{}{
				"summary":   "Список всех платежей",
				"tags":      []string{"Payments"},
				"responses": map[string]interface{}{"200": map[string]interface{}{"description": "OK"}},
			},
			"post": map[string]interface{}{
				"summary": "Создать платёж",
				"tags":    []string{"Payments"},
				"requestBody": map[string]interface{}{
					"required": true,
					"content": map[string]interface{}{
						"application/json": map[string]interface{}{
							"schema": map[string]interface{}{
								"type":     "object",
								"required": []string{"order_id", "amount"},
								"properties": map[string]interface{}{
									"order_id": map[string]interface{}{"type": "integer"},
									"amount":   map[string]interface{}{"type": "number"},
									"method":   map[string]interface{}{"type": "string", "default": "card"},
								},
							},
						},
					},
				},
				"responses": map[string]interface{}{"201": map[string]interface{}{"description": "Создано"}},
			},
		},
		"/payments/{id}": map[string]interface{}{
			"get": map[string]interface{}{
				"summary": "Получить платёж по ID",
				"tags":    []string{"Payments"},
				"parameters": []map[string]interface{}{
					{"name": "id", "in": "path", "required": true, "schema": map[string]interface{}{"type": "integer"}},
				},
				"responses": map[string]interface{}{
					"200": map[string]interface{}{"description": "OK"},
					"404": map[string]interface{}{"description": "Не найдено"},
				},
			},
		},
	},
}

func main() {
	dsn := fmt.Sprintf("host=%s port=%s user=%s password=%s dbname=%s sslmode=disable",
		env("DB_HOST", "db"), env("DB_PORT", "5432"),
		env("DB_USER", "postgres"), env("DB_PASSWORD", "postgres"),
		env("DB_NAME", "app_db"))

	var err error
	db, err = sql.Open("postgres", dsn)
	if err != nil {
		panic(err)
	}

	_, err = db.Exec(`
		CREATE TABLE IF NOT EXISTS payments (
			id SERIAL PRIMARY KEY,
			order_id INTEGER NOT NULL,
			amount FLOAT8 NOT NULL,
			method VARCHAR(50) DEFAULT 'card',
			status VARCHAR(50) DEFAULT 'pending',
			created_at TIMESTAMPTZ DEFAULT NOW()
		)
	`)
	if err != nil {
		panic(err)
	}

	gin.SetMode(gin.ReleaseMode)
	r := gin.Default()

	r.GET("/swagger/doc.json", func(c *gin.Context) { c.JSON(200, openapiSpec) })

	r.GET("/payments", listPayments)
	r.POST("/payments", createPayment)
	r.GET("/payments/:id", getPayment)

	r.Run(":8086")
}

func listPayments(c *gin.Context) {
	rows, err := db.Query("SELECT id, order_id, amount, method, status, created_at FROM payments ORDER BY created_at DESC")
	if err != nil {
		c.JSON(500, gin.H{"error": err.Error()})
		return
	}
	defer rows.Close()
	var result []map[string]interface{}
	for rows.Next() {
		var id, orderID int
		var amount float64
		var method, status, createdAt string
		rows.Scan(&id, &orderID, &amount, &method, &status, &createdAt)
		result = append(result, map[string]interface{}{
			"id": id, "order_id": orderID, "amount": amount,
			"method": method, "status": status, "created_at": createdAt,
		})
	}
	if result == nil {
		result = []map[string]interface{}{}
	}
	c.JSON(200, result)
}

func createPayment(c *gin.Context) {
	var body struct {
		OrderID int     `json:"order_id"`
		Amount  float64 `json:"amount"`
		Method  string  `json:"method"`
	}
	if err := c.ShouldBindJSON(&body); err != nil {
		c.JSON(400, gin.H{"error": err.Error()})
		return
	}
	if body.Method == "" {
		body.Method = "card"
	}
	row := db.QueryRow(
		"INSERT INTO payments (order_id, amount, method) VALUES ($1, $2, $3) RETURNING id, order_id, amount, method, status, created_at",
		body.OrderID, body.Amount, body.Method)
	var id, orderID int
	var amount float64
	var method, status, createdAt string
	if err := row.Scan(&id, &orderID, &amount, &method, &status, &createdAt); err != nil {
		c.JSON(500, gin.H{"error": err.Error()})
		return
	}
	c.JSON(201, gin.H{"id": id, "order_id": orderID, "amount": amount, "method": method, "status": status, "created_at": createdAt})
}

func getPayment(c *gin.Context) {
	id, _ := strconv.Atoi(c.Param("id"))
	row := db.QueryRow("SELECT id, order_id, amount, method, status, created_at FROM payments WHERE id = $1", id)
	var pid, orderID int
	var amount float64
	var method, status, createdAt string
	if err := row.Scan(&pid, &orderID, &amount, &method, &status, &createdAt); err != nil {
		c.JSON(404, gin.H{"error": "Платёж не найден"})
		return
	}
	c.JSON(200, gin.H{"id": pid, "order_id": orderID, "amount": amount, "method": method, "status": status, "created_at": createdAt})
}

// Dummy usage to silence import
var _ = json.Marshal
var _ = http.StatusOK
