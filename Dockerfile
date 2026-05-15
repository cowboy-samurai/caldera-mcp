FROM python:3.12-slim AS builder

WORKDIR /build

COPY pyproject.toml README.md ./
COPY caldera_mcp/ caldera_mcp/

RUN pip install --no-cache-dir --prefix=/install .


FROM python:3.12-slim

RUN useradd -m -u 1000 -s /bin/bash mcp && mkdir -p /app && chown mcp:mcp /app

WORKDIR /app

COPY --from=builder /install /usr/local

USER mcp

EXPOSE 8081

ENTRYPOINT ["caldera-mcp"]
CMD ["--transport", "sse", "--host", "0.0.0.0", "--port", "8081"]
