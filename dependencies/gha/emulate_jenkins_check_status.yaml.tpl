name: Emulate Jenkins CGE check status

on:
  push:
    branches: [ main , development ]
  pull_request:
    branches: [ main , development ]

jobs:
  validate:
    runs-on: paramount-cloud-ubuntu-amd64-latest

    steps:
      - name: Emulate Jenkins check status
        uses: vc-ccs-code/gha-cge-common/emulate_jenkins_check_status@main
        with:
          github-token: ${{ secrets.GITHUB_TOKEN }}
        if: always()