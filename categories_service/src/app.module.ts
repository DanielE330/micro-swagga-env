import { Module, OnModuleInit } from '@nestjs/common';
import { CategoriesController } from './categories.controller';
import { Pool } from 'pg';

const pool = new Pool({
  host: process.env.DB_HOST || 'db',
  port: parseInt(process.env.DB_PORT || '5432', 10),
  database: process.env.DB_NAME || 'app_db',
  user: process.env.DB_USER || 'postgres',
  password: process.env.DB_PASSWORD || 'postgres',
});

export { pool };

@Module({
  controllers: [CategoriesController],
  providers: [{ provide: 'PG_POOL', useValue: pool }],
})
export class AppModule implements OnModuleInit {
  async onModuleInit() {
    await pool.query(`
      CREATE TABLE IF NOT EXISTS categories (
        id SERIAL PRIMARY KEY,
        name VARCHAR(255) NOT NULL,
        description TEXT DEFAULT '',
        parent_id INTEGER,
        created_at TIMESTAMPTZ DEFAULT NOW()
      )
    `);
  }
}
