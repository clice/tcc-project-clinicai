"""
Centraliza as configurações da aplicação.

Este arquivo lê as variáveis de ambiente do projeto e disponibiliza
uma instância única de configuração para uso em todo o backend.
"""

from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Classe central de configurações da aplicação.

    Todas as variáveis declaradas aqui são carregadas do arquivo .env
    e podem ser usadas em qualquer parte do backend por meio da
    instância única `settings`.
    """
    
    # Nome do projeto
    project_name: str = "ClinicAI"

    # URL de conexão com o banco PostgreSQL
    database_url: str

    # Dados iniciais. ``bootstrap`` cria os catálogos estruturais e um
    # Administrador Master inicial. ``academic_demo`` acrescenta somente
    # registros fictícios para a demonstração acadêmica.
    seed_mode: Literal["bootstrap", "academic_demo"] = "bootstrap"
    bootstrap_admin_name: str = "Administrador Master"
    bootstrap_admin_email: str = "admin@clinicai.com"
    bootstrap_admin_cpf: str = "39053344705"
    bootstrap_admin_password: str = "clinicai123"
    
    # Uploads
    upload_dir: str = "uploads"
    max_upload_size_mb: int = 10
    max_image_width_px: int = 12000
    max_image_height_px: int = 12000
    max_image_pixels: int = 40_000_000

    # Serviço de IA (container separado, ver docker-compose.yml)
    ai_service_url: str = "http://ai:8001"
    ai_service_timeout_seconds: int = 120
    ai_storage_dir: str = "/app/storage"

    # Configurações de autenticação JWT
    secret_key: str
    algorithm: str
    access_token_expire_minutes: int = 60
    refresh_token_expire_minutes: int = 10080
    
    backend_cors_origins: str = ""
    
    @property
    def cors_origins(self) -> list[str]:
        return [
            origin.strip()
            for origin in self.backend_cors_origins.split(",")
            if origin.strip()
        ]

    # Configuração do Pydantic para leitura do arquivo .env
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


# Instância única de configurações da aplicação
settings = Settings()
