name: PR Validation

on:
  pull_request:
    branches:
      - main

permissions:
  contents: write
  packages: write
  pull-requests: write

jobs:
  app_image_build_check:
    uses: [[ github_org ]]/gha-docker-argocd/.github/workflows/docker_buildx.yaml@v1 
    with:
      docker-bake-path: ./docker-argo-bake.hcl
      push-image: false
    secrets: inherit