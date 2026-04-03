<?php

require __DIR__ . '/../vendor/autoload.php';

use Psr\Http\Message\ResponseInterface as Response;
use Psr\Http\Message\ServerRequestInterface as Request;
use Slim\Factory\AppFactory;

$app = AppFactory::create();
$app->addBodyParsingMiddleware();

$dbHost = getenv('DB_HOST') ?: 'db';
$dbPort = getenv('DB_PORT') ?: '5432';
$dbName = getenv('DB_NAME') ?: 'app_db';
$dbUser = getenv('DB_USER') ?: 'postgres';
$dbPass = getenv('DB_PASSWORD') ?: 'postgres';
$dsn = "pgsql:host=$dbHost;port=$dbPort;dbname=$dbName";

function getPdo(): PDO {
    global $dsn, $dbUser, $dbPass;
    static $pdo = null;
    if ($pdo === null) {
        $pdo = new PDO($dsn, $dbUser, $dbPass, [PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION]);
    }
    return $pdo;
}

// Init table
try {
    getPdo()->exec("
        CREATE TABLE IF NOT EXISTS coupons (
            id SERIAL PRIMARY KEY,
            code VARCHAR(50) NOT NULL UNIQUE,
            discount FLOAT NOT NULL,
            active BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMPTZ DEFAULT NOW()
        )
    ");
} catch (Exception $e) {
    error_log("DB init: " . $e->getMessage());
}

// OpenAPI spec
$app->get('/api/doc.json', function (Request $req, Response $res) {
    $spec = [
        'openapi' => '3.0.0',
        'info' => [
            'title' => 'Coupons Service',
            'version' => '1.0.0',
            'description' => 'Промокоды и скидки (PHP / Slim)',
        ],
        'paths' => [
            '/coupons' => [
                'get' => [
                    'summary' => 'Список всех купонов',
                    'tags' => ['Coupons'],
                    'responses' => ['200' => ['description' => 'OK']],
                ],
                'post' => [
                    'summary' => 'Создать купон',
                    'tags' => ['Coupons'],
                    'requestBody' => [
                        'required' => true,
                        'content' => [
                            'application/json' => [
                                'schema' => [
                                    'type' => 'object',
                                    'required' => ['code', 'discount'],
                                    'properties' => [
                                        'code' => ['type' => 'string', 'example' => 'SALE20'],
                                        'discount' => ['type' => 'number', 'example' => 20.0],
                                    ],
                                ],
                            ],
                        ],
                    ],
                    'responses' => ['201' => ['description' => 'Создано']],
                ],
            ],
            '/coupons/{id}' => [
                'get' => [
                    'summary' => 'Получить купон по ID',
                    'tags' => ['Coupons'],
                    'parameters' => [
                        ['name' => 'id', 'in' => 'path', 'required' => true, 'schema' => ['type' => 'integer']],
                    ],
                    'responses' => [
                        '200' => ['description' => 'OK'],
                        '404' => ['description' => 'Не найдено'],
                    ],
                ],
            ],
        ],
    ];
    $res->getBody()->write(json_encode($spec, JSON_UNESCAPED_UNICODE));
    return $res->withHeader('Content-Type', 'application/json');
});

$app->get('/coupons', function (Request $req, Response $res) {
    $rows = getPdo()->query('SELECT * FROM coupons ORDER BY created_at DESC')->fetchAll(PDO::FETCH_ASSOC);
    $res->getBody()->write(json_encode($rows));
    return $res->withHeader('Content-Type', 'application/json');
});

$app->get('/coupons/{id}', function (Request $req, Response $res, array $args) {
    $stmt = getPdo()->prepare('SELECT * FROM coupons WHERE id = ?');
    $stmt->execute([$args['id']]);
    $row = $stmt->fetch(PDO::FETCH_ASSOC);
    if (!$row) {
        $res->getBody()->write(json_encode(['error' => 'Купон не найден']));
        return $res->withStatus(404)->withHeader('Content-Type', 'application/json');
    }
    $res->getBody()->write(json_encode($row));
    return $res->withHeader('Content-Type', 'application/json');
});

$app->post('/coupons', function (Request $req, Response $res) {
    $body = $req->getParsedBody();
    $stmt = getPdo()->prepare('INSERT INTO coupons (code, discount) VALUES (?, ?) RETURNING *');
    $stmt->execute([$body['code'], $body['discount']]);
    $row = $stmt->fetch(PDO::FETCH_ASSOC);
    $res->getBody()->write(json_encode($row));
    return $res->withStatus(201)->withHeader('Content-Type', 'application/json');
});

$app->run();
