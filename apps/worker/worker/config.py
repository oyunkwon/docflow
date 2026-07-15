from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(extra="ignore")

    database_url: str = "postgresql+psycopg://docflow:docflow@localhost:5432/docflow"
    s3_bucket: str = "docflow-dev-documents"
    sqs_queue_url: str = ""
    aws_region: str = "ap-northeast-2"

    # 로컬 전용. 비어 있으면 실제 AWS로 붙는다.
    aws_endpoint_url: str = ""

    # 롱폴링 대기 시간(초)
    wait_time_seconds: int = 20


settings = Settings()
