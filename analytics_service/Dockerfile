FROM rust:1.86-slim-bookworm AS build
RUN apt-get update && apt-get install -y pkg-config libssl-dev curl && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY Cargo.toml .
RUN mkdir src && echo 'fn main(){}' > src/main.rs && cargo build --release 2>/dev/null; true
COPY src/ ./src/
RUN cargo build --release

FROM debian:bookworm-slim
RUN apt-get update && apt-get install -y libssl3 ca-certificates && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY --from=build /app/target/release/analytics_service .
EXPOSE 8088
CMD ["./analytics_service"]
