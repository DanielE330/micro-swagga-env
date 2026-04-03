import 'package:dart_frog/dart_frog.dart';

// GET / — health check
Response onRequest(RequestContext context) {
  return Response.json(
    body: {'status': 'ok', 'service': 'products_service'},
  );
}
