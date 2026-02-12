# commit-workflow.md - Git & Commit Conventions

## Branch Strategy

### Branch Types
- main/ — Production-ready (auto-deploy to Vercel)
- develop/ — Integration branch
  - feature/* — New features
  - bugfix/* — Bug fixes
  - refactor/* — Code restructuring
  - llm/* — LLM integration changes

## Commit Messages

### Format (Conventional Commits)
```
<type>(<scope>): <subject>

<body>

<footer>
```

### Commit Types
- **feat**: New feature
- **fix**: Bug fix
- **refactor**: Code restructuring
- **perf**: Performance improvement
- **test**: Add/update tests
- **docs**: Documentation
- **style**: Code formatting
- **chore**: Dependencies, tooling
- **ci**: CI/CD configuration

### Scope
- frontend, backend, api, llm, workout, fitness, auth, ui, docker, db

### Subject Line
- Imperative mood: "add", "fix", "improve"
- Lowercase first letter
- No period at end
- <= 50 characters

## Pull Request Workflow

1. **Author**: Create PR from feature branch → develop
2. **Reviewer**: Check logic, tests, LLM fallback handling
3. **Author**: Address feedback
4. **Merge**: Squash for clean history
5. **Deploy**: Merge develop → main (auto-deploy Vercel)

## Release Process

- Version: MAJOR.MINOR.PATCH (semver)
- Tag: git tag -a vX.Y.Z
- Release notes with changelog (include LLM model updates)
