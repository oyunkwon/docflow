terraform {
  backend "s3" {
    bucket       = "docflow-tfstate-676591241328"
    key          = "dev/terraform.tfstate"
    region       = "ap-northeast-2"
    use_lockfile = true
    encrypt      = true
  }
}
