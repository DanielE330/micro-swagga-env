package com.example.inventory;

import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.Map;

@RestController
@RequestMapping("/inventory")
@Tag(name = "Inventory")
public class InventoryController {

    private final JdbcTemplate jdbc;

    public InventoryController(JdbcTemplate jdbc) {
        this.jdbc = jdbc;
    }

    @GetMapping
    @Operation(summary = "Список всех остатков")
    public List<Map<String, Object>> list() {
        return jdbc.queryForList("SELECT * FROM inventory ORDER BY id");
    }

    @GetMapping("/{id}")
    @Operation(summary = "Получить запись по ID")
    public ResponseEntity<?> getById(@PathVariable int id) {
        var rows = jdbc.queryForList("SELECT * FROM inventory WHERE id = ?", id);
        if (rows.isEmpty()) return ResponseEntity.status(HttpStatus.NOT_FOUND).body(Map.of("error", "Не найдено"));
        return ResponseEntity.ok(rows.get(0));
    }

    @PostMapping
    @Operation(summary = "Добавить запись о складском остатке")
    public ResponseEntity<?> create(@RequestBody Map<String, Object> body) {
        int productId = (int) body.get("product_id");
        String warehouse = (String) body.get("warehouse");
        int quantity = body.containsKey("quantity") ? (int) body.get("quantity") : 0;
        var result = jdbc.queryForMap(
            "INSERT INTO inventory (product_id, warehouse, quantity) VALUES (?, ?, ?) RETURNING *",
            productId, warehouse, quantity
        );
        return ResponseEntity.status(HttpStatus.CREATED).body(result);
    }
}
