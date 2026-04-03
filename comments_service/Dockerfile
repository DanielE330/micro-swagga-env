FROM ruby:3.3-slim
RUN apt-get update && apt-get install -y build-essential libpq-dev && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY Gemfile ./
RUN bundle install --without development test
COPY . .
EXPOSE 3003
CMD ["bundle", "exec", "puma", "-b", "tcp://0.0.0.0:3003", "config.ru"]
