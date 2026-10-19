"""Config จาก environment variables (12-factor, ADR-0013)

image เดียวกันใช้ได้ทั้ง docker-compose, Kubernetes และ CI เปลี่ยนแค่ env
เช่น OLLAMA_URL=http://ollama:11434 (compose) หรือ http://ollama.ai.svc:11434 (k8s)
"""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    ollama_url: str = "http://localhost:11434"
    qdrant_url: str = "http://localhost:6333"
    collection: str = "docs"

    chat_model: str = "qwen2.5:1.5b"
    embed_model: str = "bge-m3"
    embed_dim: int = 1024  # ต้องตรงกับ embed_model (bge-m3 = 1024)

    top_k: int = 4
    chunk_size: int = 800
    chunk_overlap: int = 150
    embed_batch: int = 16
    request_timeout: float = 180.0


settings = Settings()
