'use strict';

const Hapi = require('@hapi/hapi');
const Inert = require('@hapi/inert');
const Vision = require('@hapi/vision');
const HapiSwagger = require('hapi-swagger');
const Joi = require('joi');
const { Pool } = require('pg');

const pool = new Pool({
  host: process.env.DB_HOST || 'db',
  port: parseInt(process.env.DB_PORT || '5432', 10),
  database: process.env.DB_NAME || 'app_db',
  user: process.env.DB_USER || 'postgres',
  password: process.env.DB_PASSWORD || 'postgres',
});

const init = async () => {
  await pool.query(`
    CREATE TABLE IF NOT EXISTS tags (
      id SERIAL PRIMARY KEY,
      name VARCHAR(100) NOT NULL UNIQUE,
      color VARCHAR(7) DEFAULT '#000000',
      created_at TIMESTAMPTZ DEFAULT NOW()
    )
  `);

  const server = Hapi.server({ port: 3002, host: '0.0.0.0' });

  await server.register([
    Inert,
    Vision,
    {
      plugin: HapiSwagger,
      options: {
        info: { title: 'Tags Service', version: '1.0.0', description: 'Теги (Hapi)' },
        documentationPath: '/doc',
        jsonPath: '/swagger.json',
      },
    },
  ]);

  server.route([
    {
      method: 'GET',
      path: '/tags',
      options: {
        tags: ['api'],
        description: 'Список всех тегов',
        handler: async () => {
          const { rows } = await pool.query('SELECT * FROM tags ORDER BY name');
          return rows;
        },
      },
    },
    {
      method: 'POST',
      path: '/tags',
      options: {
        tags: ['api'],
        description: 'Создать тег',
        validate: {
          payload: Joi.object({
            name: Joi.string().required().example('sale'),
            color: Joi.string().default('#000000').example('#ff5722'),
          }),
        },
        handler: async (req) => {
          const { name, color } = req.payload;
          const { rows } = await pool.query(
            'INSERT INTO tags (name, color) VALUES ($1, $2) RETURNING *',
            [name, color || '#000000'],
          );
          return rows[0];
        },
      },
    },
    {
      method: 'DELETE',
      path: '/tags/{id}',
      options: {
        tags: ['api'],
        description: 'Удалить тег',
        validate: {
          params: Joi.object({ id: Joi.number().integer().required() }),
        },
        handler: async (req, h) => {
          const { rows } = await pool.query(
            'DELETE FROM tags WHERE id = $1 RETURNING id',
            [req.params.id],
          );
          if (rows.length === 0) return h.response({ error: 'Тег не найден' }).code(404);
          return { message: 'Тег удалён', id: req.params.id };
        },
      },
    },
  ]);

  await server.start();
  console.log(`[tags_service] running on ${server.info.uri}`);
};

init();
