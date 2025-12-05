# LangGraph migration agent
- Use TypedDict for MigrationState
- Sequential workflow: clone → analyze → update → validate → workflows → push  
- Human-in-loop interrupt after dockerfile validation
- Track repo_path in state across all nodes
- Always validate git status before push
- Use subprocess.run for git operations with check=True
- Temp directories: /tmp/{uuid}
- Feature branch: feat/gha-migrate