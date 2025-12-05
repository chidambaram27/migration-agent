# Define variables that will come from GitHub
variable "GITHUB_RUN_NUMBER" {
  default = "0"
}

variable "IMAGE_VERSION" {
  default = "1.0"
}

variable "IMAGE_PREFIX" {
  default = "ghcr.io/[[ github_org ]]/[[ repo_name ]]"
}

variable "GITHUB_REF_NAME" {
  default = ""
}

variable "GITHUB_BASE_REF" {
  default = ""
}

target "app" {

  dockerfile = "[[ dockerfile_path ]]"

  tags = [
    GITHUB_BASE_REF == "master" || GITHUB_REF_NAME == "master" || GITHUB_BASE_REF == "main" || GITHUB_REF_NAME == "main" ?
    "${IMAGE_PREFIX}/app:${IMAGE_VERSION}.${GITHUB_RUN_NUMBER}" : "${IMAGE_PREFIX}/app:${IMAGE_VERSION}.${GITHUB_RUN_NUMBER}-dev",
  ]
}

group "default" {
  targets = ["app"]
}