FROM python:3.11-slim

WORKDIR /app

# system deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    poppler-utils \
    tesseract-ocr \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

# install python deps
# torch takes a while to install
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ ./app/

# pre-download the embedding model so it's baked into the image
# saves time on first request (otherwise it downloads at runtime)
RUN python3 -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')" \
    || echo "model download failed - will retry at runtime"

RUN mkdir -p /app/uploads

EXPOSE 8003

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8003", "--workers", "1"]
