from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore", env_ignore_empty=True)

    anthropic_api_key: str = ""
    voyage_api_key: str = ""

    database_url: str = "postgresql+psycopg://cadence:cadence@db:5432/cadence"
    storage_dir: str = "/app/storage"

    claude_model: str = "claude-sonnet-4-6"
    voyage_model: str = "voyage-3"
    embedding_dim: int = 1024

    cors_origins: str = "https://cadence-mauve-ten.vercel.app,http://localhost:3000,http://localhost:3001"

    # Clerk publishable key — used to derive the JWKS URL for token verification.
    # Same value as NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY on the frontend.
    clerk_publishable_key: str = ""

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


settings = Settings()
