const express = require('express');
const { pool } = require('../db');

const router = express.Router();

const VALID_STATUSES = ['pending', 'confirmed', 'shipped', 'delivered', 'cancelled'];

// GET /orders — список всех заказов
router.get('/', async (_req, res) => {
  try {
    const { rows } = await pool.query(
      'SELECT * FROM orders ORDER BY created_at DESC',
    );
    res.json(rows);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// GET /orders/:id — получить заказ по ID
router.get('/:id', async (req, res) => {
  const id = parseInt(req.params.id, 10);
  if (Number.isNaN(id)) {
    return res.status(400).json({ error: 'ID должен быть числом' });
  }
  try {
    const { rows } = await pool.query(
      'SELECT * FROM orders WHERE id = $1',
      [id],
    );
    if (rows.length === 0) {
      return res.status(404).json({ error: 'Заказ не найден' });
    }
    res.json(rows[0]);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// POST /orders — создать заказ
router.post('/', async (req, res) => {
  const { product_id, user_id, quantity = 1, total_price } = req.body;

  if (!product_id || !user_id || total_price === undefined) {
    return res.status(400).json({
      error: 'Поля product_id, user_id и total_price обязательны',
    });
  }

  try {
    const { rows } = await pool.query(
      `INSERT INTO orders (product_id, user_id, quantity, total_price)
       VALUES ($1, $2, $3, $4) RETURNING *`,
      [product_id, user_id, quantity, total_price],
    );
    res.status(201).json(rows[0]);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// PATCH /orders/:id/status — изменить статус заказа
router.patch('/:id/status', async (req, res) => {
  const id = parseInt(req.params.id, 10);
  if (Number.isNaN(id)) {
    return res.status(400).json({ error: 'ID должен быть числом' });
  }

  const { status } = req.body;
  if (!status || !VALID_STATUSES.includes(status)) {
    return res.status(400).json({
      error: `Допустимые статусы: ${VALID_STATUSES.join(', ')}`,
    });
  }

  try {
    const { rows } = await pool.query(
      'UPDATE orders SET status = $1 WHERE id = $2 RETURNING *',
      [status, id],
    );
    if (rows.length === 0) {
      return res.status(404).json({ error: 'Заказ не найден' });
    }
    res.json(rows[0]);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

module.exports = router;
