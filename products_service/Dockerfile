FROM dart:stable AS build

WORKDIR /app

ENV PATH="${PATH}:/root/.pub-cache/bin"

RUN dart pub global activate dart_frog_cli

COPY pubspec.yaml ./
RUN dart pub get --no-precompile

COPY . .
RUN dart pub get

RUN dart_frog build
RUN dart compile exe build/bin/server.dart -o build/bin/server

FROM scratch

COPY --from=build /runtime/ /
COPY --from=build /app/build/bin/server /app/bin/server

EXPOSE 8080

CMD ["/app/bin/server"]
