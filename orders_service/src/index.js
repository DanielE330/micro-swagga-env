const express = require('express');
const { initDb } = require('./db');
const ordersRouter = require('./routes/orders');

const app = express();
app.use(express.json());

// GET /openapi.json — OpenAPI-спека для docs_service
app.get('/openapi.json', (_req, res) => {
  res.json({
    openapi: '3.0.0',
    info: {
      title: 'Orders Service',
      version: '1.0.0',
      description: 'Управление заказами',
    },
    paths: {
      '/orders': {
        get: {
          summary: 'Список всех заказов',
          tags: ['Orders'],
          responses: { 200: { description: 'Список заказов' } },
        },
        post: {
          summary: 'Создать заказ',
          tags: ['Orders'],
          requestBody: {
            required: true,
            content: {
              'application/json': {
                schema: {
                  type: 'object',
                  required: ['product_id', 'user_id', 'total_price'],
                  properties: {
                    product_id: { type: 'integer', example: 1 },
                    user_id: { type: 'integer', example: 5 },
                    quantity: { type: 'integer', default: 1 },
                    total_price: { type: 'number', example: 59999.99 },
                  },
                },
              },
            },
          },
          responses: {
            201: { description: 'Заказ создан' },
            400: { description: 'Некорректные данные' },
          },
        },
      },
      '/orders/{id}': {
        get: {
          summary: 'Получить заказ по ID',
          tags: ['Orders'],
          parameters: [
            { name: 'id', in: 'path', required: true, schema: { type: 'integer' } },
          ],
          responses: {
            200: { description: 'Заказ найден' },
            404: { description: 'Заказ не найден' },
          },
        },
      },
      '/orders/{id}/status': {
        patch: {
          summary: 'Изменить статус заказа',
          tags: ['Orders'],
          parameters: [
            { name: 'id', in: 'path', required: true, schema: { type: 'integer' } },
          ],
          requestBody: {
            required: true,
            content: {
              'application/json': {
                schema: {
                  type: 'object',
                  properties: {
                    status: {
                      type: 'string',
                      enum: ['pending', 'confirmed', 'shipped', 'delivered', 'cancelled'],
                    },
                  },
                },
              },
            },
          },
          responses: {
            200: { description: 'Статус обновлён' },
            404: { description: 'Заказ не найден' },
          },
        },
      },
    },
  });
});

// GET / — health check
app.get('/', (_req, res) => {
  res.json({ status: 'ok', service: 'orders_service' });
});

app.use('/orders', ordersRouter);

const PORT = process.env.PORT || 3000;

initDb()
  .then(() => {
    app.listen(PORT, () => {
      console.log(`[orders_service] listening on port ${PORT}`);
    });
  })
  .catch((err) => {
    console.error('[orders_service] DB init failed:', err);
    process.exit(1);
  });
