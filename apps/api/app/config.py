from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # 비어 있으면 DB에 의존하지 않는다. DB 없이도 Pod가 뜨고 health가 통과해야 한다.
    # RDS를 붙이는 단계에서 overlay가 DATABASE_URL을 채우면 그때부터 DB 기능이 켜진다.
    database_url: str = ""
    s3_bucket: str = "docflow-dev-documents"
    sqs_queue_url: str = ""
    aws_region: str = "ap-northeast-2"

    # 로컬 전용. 비어 있으면 실제 AWS로 붙는다.
    aws_endpoint_url: str = ""
    # presigned URL을 브라우저가 접근할 host. 비면 aws_endpoint_url을 쓴다.
    s3_public_endpoint: str = ""

    presign_expiry: int = 3600


settings = Settings()
