name: App Image Build

on:
  push:
    branches:
      - main

permissions:
  contents: write
  packages: write
  pull-requests: write

jobs:
  app_image_build:
    uses: [[ github_org ]]/gha-docker-argocd/.github/workflows/docker_buildx.yaml@v1 
    secrets: inherit 
    with:
      docker-bake-path: ./docker-argo-bake.hcl
      push-image: true