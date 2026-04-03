import 'dart:convert';
import 'package:dart_frog/dart_frog.dart';

Response onRequest(RequestContext context) {
  const spec = {
    'openapi': '3.0.0',
    'info': {
      'title': 'Products Service',
      'version': '1.0.0',
      'description': 'Каталог товаров',
    },
    'paths': {
      '/products': {
        'get': {
          'summary': 'Список всех товаров',
          'tags': ['Products'],
          'responses': {
            '200': {'description': 'Список товаров'},
          },
        },
        'post': {
          'summary': 'Создать товар',
          'tags': ['Products'],
          'requestBody': {
            'required': true,
            'content': {
              'application/json': {
                'schema': {
                  'type': 'object',
                  'required': ['name', 'price'],
                  'properties': {
                    'name': {'type': 'string', 'example': 'Ноутбук'},
                    'description': {'type': 'string'},
                    'price': {'type': 'number', 'example': 59999.99},
                    'stock': {'type': 'integer', 'default': 0},
                  },
                },
              },
            },
          },
          'responses': {
            '201': {'description': 'Товар создан'},
            '400': {'description': 'Некорректные данные'},
          },
        },
      },
      '/products/{id}': {
        'get': {
          'summary': 'Получить товар по ID',
          'tags': ['Products'],
          'parameters': [
            {
              'name': 'id',
              'in': 'path',
              'required': true,
              'schema': {'type': 'integer'},
            },
          ],
          'responses': {
            '200': {'description': 'Товар найден'},
            '404': {'description': 'Товар не найден'},
          },
        },
        'delete': {
          'summary': 'Удалить товар',
          'tags': ['Products'],
          'parameters': [
            {
              'name': 'id',
              'in': 'path',
              'required': true,
              'schema': {'type': 'integer'},
            },
          ],
          'responses': {
            '200': {'description': 'Товар удалён'},
            '404': {'description': 'Товар не найден'},
          },
        },
      },
    },
  };

  return Response(
    headers: {'content-type': 'application/json; charset=utf-8'},
    body: jsonEncode(spec),
  );
}
