# 🤝 Contributing to PEIP — SUNHACKS

Welcome! This guide explains exactly how to collaborate on this project using GitHub. Follow these steps carefully.

---

## 👥 Team Setup

| Role | GitHub Username | Responsibility |
|:---|:---|:---|
| Owner | Albertpradeep-007 | Architecture, Merge approvals |
| Collaborator | JungliCode | Features, Bug fixes, PRs |

---

## 🌿 Branch Strategy

We use a **feature-branch workflow**. Never push directly to `main`.

```
main        ← stable, production-ready (protected)
develop     ← integration branch (merge features here first)
feature/*   ← new features
fix/*       ← bug fixes
docs/*      ← documentation only
```

---

## 🔄 Step-by-Step Workflow

### 1. Clone the repo (first time only)

```bash
git clone https://github.com/Albertpradeep-007/SUNHACKS-agentic-ai.git
cd SUNHACKS-agentic-ai
```

### 2. Always pull latest before starting work

```bash
git checkout develop
git pull origin develop
```

### 3. Create your feature branch

```bash
# For a new feature:
git checkout -b feature/your-feature-name

# For a bug fix:
git checkout -b fix/bug-description

# For docs:
git checkout -b docs/what-you-are-documenting
```

### 4. Make your changes, add & commit

```bash
git add .
git commit -m "feat: describe what you added"
```

### 5. Push your branch to GitHub

```bash
git push origin feature/your-feature-name
```

### 6. Open a Pull Request on GitHub

1. Go to https://github.com/Albertpradeep-007/SUNHACKS-agentic-ai
2. Click **"Compare & pull request"**
3. Set base branch to `develop` (NOT `main`)
4. Fill in the PR description
5. Request a review from the other person
6. Wait for approval before merging

---

## ✍️ Commit Message Convention

We follow [Conventional Commits](https://www.conventionalcommits.org/):

```
feat: add new risk scoring algorithm
fix: resolve dashboard crash on empty repo
docs: update setup instructions
refactor: simplify agent handoff logic
test: add unit tests for RiskAgent
chore: update .gitignore
```

**Format:** `type: short description (max 72 chars)`

---

## ⚠️ Important Rules

- ❌ **Never** push directly to `main`
- ❌ **Never** force push (`git push --force`)
- ✅ **Always** pull latest before starting work
- ✅ **Always** create a new branch per feature/fix
- ✅ **Always** write clear commit messages
- ✅ **Always** open a PR for review before merging

---

## 🔀 Resolving Merge Conflicts

If you get a conflict:

```bash
# Pull latest develop into your branch
git fetch origin
git merge origin/develop

# Fix the conflicts in your editor, then:
git add .
git commit -m "fix: resolve merge conflict with develop"
git push origin feature/your-feature-name
```

---

## 📦 Keeping Your Fork Updated (if forked)

```bash
git remote add upstream https://github.com/Albertpradeep-007/SUNHACKS-agentic-ai.git
git fetch upstream
git checkout develop
git merge upstream/develop
```

---

## 🚀 Quick Reference

```bash
# Start work
git checkout develop
git pull origin develop
git checkout -b feature/my-feature

# Do your work...

# Save work
git add .
git commit -m "feat: my feature"
git push origin feature/my-feature

# Then open a PR on GitHub → target: develop
```

---

*Questions? Open a GitHub Issue or reach out to the team.*
