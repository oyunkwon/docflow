# ECR 저장소. 환경 구분 없음(이미지는 dev→prod로 승격된다).
# dev를 매일 destroy해도 이미지가 살아남도록 dev state가 아닌 shared state에 둔다.

locals {
  # 이름은 AGENTS.md 네이밍 규칙: 환경 접두사 없이 docflow-{app}
  repositories = [
    "docflow-api",
    "docflow-worker",
    "docflow-frontend",
  ]
}

resource "aws_ecr_repository" "this" {
  for_each = toset(local.repositories)

  name = each.value

  # 태그를 덮어쓰지 못하게 한다. 같은 SHA 태그는 항상 같은 이미지다.
  image_tag_mutability = "IMMUTABLE"

  image_scanning_configuration {
    scan_on_push = true
  }
}

# 라이프사이클: 태그 없는 이미지는 7일 후 삭제, 태그 있는 이미지는 최근 20개만 유지.
resource "aws_ecr_lifecycle_policy" "this" {
  for_each = aws_ecr_repository.this

  repository = each.value.name

  policy = jsonencode({
    rules = [
      {
        rulePriority = 1
        description  = "Expire untagged images after 7 days"
        selection = {
          tagStatus   = "untagged"
          countType   = "sinceImagePushed"
          countUnit   = "days"
          countNumber = 7
        }
        action = { type = "expire" }
      },
      {
        rulePriority = 2
        description  = "Keep only the 20 most recent tagged images"
        selection = {
          tagStatus      = "tagged"
          tagPatternList = ["*"]
          countType      = "imageCountMoreThan"
          countNumber    = 20
        }
        action = { type = "expire" }
      },
    ]
  })
}
