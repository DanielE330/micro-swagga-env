import { Controller, Get, Post, Param, Body, Inject, HttpCode, NotFoundException, BadRequestException } from '@nestjs/common';
import { ApiTags, ApiOperation, ApiBody, ApiParam } from '@nestjs/swagger';
import { Pool } from 'pg';

class CreateCategoryDto {
  name: string;
  description?: string;
  parent_id?: number;
}

@ApiTags('Categories')
@Controller('categories')
export class CategoriesController {
  constructor(@Inject('PG_POOL') private readonly pool: Pool) {}

  @Get()
  @ApiOperation({ summary: 'Список всех категорий' })
  async findAll() {
    const { rows } = await this.pool.query('SELECT * FROM categories ORDER BY id');
    return rows;
  }

  @Get(':id')
  @ApiOperation({ summary: 'Получить категорию по ID' })
  @ApiParam({ name: 'id', type: Number })
  async findOne(@Param('id') id: string) {
    const { rows } = await this.pool.query('SELECT * FROM categories WHERE id = $1', [id]);
    if (rows.length === 0) throw new NotFoundException('Категория не найдена');
    return rows[0];
  }

  @Post()
  @HttpCode(201)
  @ApiOperation({ summary: 'Создать категорию' })
  @ApiBody({
    schema: {
      type: 'object',
      required: ['name'],
      properties: {
        name: { type: 'string', example: 'Электроника' },
        description: { type: 'string' },
        parent_id: { type: 'integer', nullable: true },
      },
    },
  })
  async create(@Body() body: CreateCategoryDto) {
    if (!body.name) throw new BadRequestException('Поле name обязательно');
    const { rows } = await this.pool.query(
      'INSERT INTO categories (name, description, parent_id) VALUES ($1, $2, $3) RETURNING *',
      [body.name, body.description || '', body.parent_id || null],
    );
    return rows[0];
  }
}
