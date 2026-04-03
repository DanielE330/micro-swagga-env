require 'grape'
require 'grape-swagger'
require 'pg'
require 'json'

def db_conn
  PG.connect(
    host: ENV.fetch('DB_HOST', 'db'),
    port: ENV.fetch('DB_PORT', '5432').to_i,
    dbname: ENV.fetch('DB_NAME', 'app_db'),
    user: ENV.fetch('DB_USER', 'postgres'),
    password: ENV.fetch('DB_PASSWORD', 'postgres')
  )
end

# Init table
begin
  conn = db_conn
  conn.exec(<<~SQL)
    CREATE TABLE IF NOT EXISTS comments (
      id SERIAL PRIMARY KEY,
      product_id INTEGER NOT NULL,
      user_id INTEGER NOT NULL,
      body TEXT NOT NULL,
      created_at TIMESTAMPTZ DEFAULT NOW()
    )
  SQL
  conn.close
rescue => e
  $stderr.puts "DB init error: #{e.message}"
end

class CommentsAPI < Grape::API
  format :json
  prefix :api

  resource :comments do
    desc 'Список всех комментариев'
    get do
      conn = db_conn
      rows = conn.exec('SELECT * FROM comments ORDER BY created_at DESC').to_a
      conn.close
      rows
    end

    desc 'Создать комментарий'
    params do
      requires :product_id, type: Integer
      requires :user_id, type: Integer
      requires :body, type: String
    end
    post do
      conn = db_conn
      res = conn.exec_params(
        'INSERT INTO comments (product_id, user_id, body) VALUES ($1, $2, $3) RETURNING *',
        [params[:product_id], params[:user_id], params[:body]]
      )
      conn.close
      res.first
    end

    desc 'Получить комментарий по ID'
    params do
      requires :id, type: Integer
    end
    route_param :id do
      get do
        conn = db_conn
        res = conn.exec_params('SELECT * FROM comments WHERE id = $1', [params[:id]])
        conn.close
        error!('Комментарий не найден', 404) if res.ntuples.zero?
        res.first
      end
    end
  end

  add_swagger_documentation(
    info: {
      title: 'Comments Service',
      description: 'Комментарии (Ruby / Grape)',
      version: '1.0.0'
    },
    doc_version: '1.0.0'
  )
end
