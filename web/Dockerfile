FROM python:3.11-slim

WORKDIR /app
COPY . /app

# Install system dependencies for common Python packages
RUN apt-get update -y && \
    apt-get install -y --no-install-recommends build-essential libpq-dev 

# Upgrade pip & install requirements
RUN pip install --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r requirements.txt

CMD ["python", "app.py"]
