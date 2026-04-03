import 'package:dart_frog/dart_frog.dart';
import 'package:postgres/postgres.dart';
import 'package:products_service/database.dart';

/// GET    /products/[id] — получить товар по ID
/// DELETE /products/[id] — удалить товар
Future<Response> onRequest(RequestContext context, String id) async {
  final productId = int.tryParse(id);
  if (productId == null) {
    return Response.json(
      statusCode: 400,
      body: {'error': 'ID должен быть числом'},
    );
  }

  switch (context.request.method) {
    case HttpMethod.get:
      return _getById(productId);
    case HttpMethod.delete:
      return _delete(productId);
    default:
      return Response(statusCode: 405);
  }
}

Future<Response> _getById(int id) async {
  try {
    final db = await getDatabase();
    final result = await db.execute(
      Sql.named('SELECT * FROM products WHERE id = @id'),
      parameters: {'id': id},
    );
    if (result.isEmpty) {
      return Response.json(
        statusCode: 404,
        body: {'error': 'Товар не найден'},
      );
    }
    return Response.json(body: rowToMap(result.first.toColumnMap()));
  } catch (e) {
    return Response.json(statusCode: 500, body: {'error': e.toString()});
  }
}

Future<Response> _delete(int id) async {
  try {
    final db = await getDatabase();
    final result = await db.execute(
      Sql.named('DELETE FROM products WHERE id = @id RETURNING id'),
      parameters: {'id': id},
    );
    if (result.isEmpty) {
      return Response.json(
        statusCode: 404,
        body: {'error': 'Товар не найден'},
      );
    }
    return Response.json(body: {'message': 'Товар удалён', 'id': id});
  } catch (e) {
    return Response.json(statusCode: 500, body: {'error': e.toString()});
  }
}
