# Amazon Inventory Template Converter — containerized
FROM python:3.12-slim

# Prevents Python from writing .pyc files & enables unbuffered output
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Copy metadata first for better layer caching
COPY pyproject.toml README.md LICENSE ./
COPY src ./src

# Install package
RUN pip install --no-cache-dir --upgrade pip && pip install --no-cache-dir .

# Default entrypoint + help
ENTRYPOINT ["aitc"]
CMD ["--help"]
