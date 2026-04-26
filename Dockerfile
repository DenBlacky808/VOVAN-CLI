FROM python:3.11-slim

WORKDIR /app

COPY pyproject.toml README.md /app/
COPY vovan /app/vovan

RUN pip install --no-cache-dir .

ENTRYPOINT ["vovan"]
CMD ["worker"]
