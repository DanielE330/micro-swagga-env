import 'package:dart_frog/dart_frog.dart';
import 'package:postgres/postgres.dart';
import 'package:products_service/database.dart';

/// GET  /products — список всех товаров
/// POST /products — создать товар
Future<Response> onRequest(RequestContext context) async {
  switch (context.request.method) {
    case HttpMethod.get:
      return _getAll();
    case HttpMethod.post:
      return _create(context);
    default:
      return Response(statusCode: 405);
  }
}

Future<Response> _getAll() async {
  try {
    final db = await getDatabase();
    final result = await db.execute(
      'SELECT * FROM products ORDER BY created_at DESC',
    );
    final products = result.map((row) => rowToMap(row.toColumnMap())).toList();
    return Response.json(body: products);
  } catch (e) {
    return Response.json(statusCode: 500, body: {'error': e.toString()});
  }
}

Future<Response> _create(RequestContext context) async {
  try {
    final body = await context.request.json() as Map<String, dynamic>;
    final name = body['name'] as String?;
    final description = body['description'] as String?;
    final price = (body['price'] as num?)?.toDouble();
    final stock = (body['stock'] as num?)?.toInt() ?? 0;

    if (name == null || name.isEmpty || price == null) {
      return Response.json(
        statusCode: 400,
        body: {'error': 'Поля name и price обязательны'},
      );
    }

    final db = await getDatabase();
    final result = await db.execute(
      Sql.named(
        'INSERT INTO products (name, description, price, stock) '
        'VALUES (@name, @desc, @price, @stock) RETURNING *',
      ),
      parameters: {
        'name': name,
        'desc': description,
        'price': price,
        'stock': stock,
      },
    );

    return Response.json(
      statusCode: 201,
      body: rowToMap(result.first.toColumnMap()),
    );
  } catch (e) {
    return Response.json(statusCode: 500, body: {'error': e.toString()});
  }
}
