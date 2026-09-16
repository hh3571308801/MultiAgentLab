# Publishing to GitHub Guide

> The local repo is ready (`main` branch, first commit done). Below are the full steps to push it to GitHub.

---

## 1. Create the remote repository (2 minutes)

1. Open https://github.com/new
2. Fill in the fields:

| Field | Value |
|-------|-------|
| **Repository name** | `MultiAgentLab` |
| **Description** | `An observable & evaluable multi-LLM-agent collaboration framework with full trajectory recording` |
| **Visibility** | ✅ **Public** (open-source projects must be public) |
| **Initialize this repository with** | ❌ **Check none** (don't check README / .gitignore / license, otherwise they'll conflict with local) |

3. Click **Create repository**

---

## 2. Push to GitHub (1 minute)

After creating, you'll see a command hint page. **Only look at the "…or push an existing repository" section**:

```bash
cd C:\Users\35713\Desktop\MultiAgentLab

# Replace <your-github-username> with the actual one (this machine is configured as hh3571308801)
git remote add origin https://github.com/<your-github-username>/MultiAgentLab.git

git branch -M main
git push -u origin main
```

A login window will pop up during push (browser authorization or Personal Access Token).
**The first push to GitHub requires a PAT**. If you don't have one yet:
GitHub → top-right avatar → Settings → Developer settings → Personal access tokens → Tokens (classic) → Generate new token → check `repo` permission → copy it and paste it as the password.

---

## 3. Repository settings (make the project "look professional", 5 minutes)

After pushing, go to the repo page, top-right **⚙️ Settings** next to the **About** (pencil icon), and fill in:

**Description**:
```
An observable & evaluable multi-LLM-agent collaboration framework with full trajectory recording.
Planner → Executor → Critic loop | Multi-provider (DeepSeek/OpenAI/Qwen) | FastAPI | 33 tests
```

**Topics** (add one by one, 8 in total):
```
llm  agent  multi-agent  llm-agent  trajectory  evaluation  fastapi  python
```

**Check**:
- ☑️ Releases
- ☑️ Packages (optional)
- ☑️ Discussions (**recommended**, for community feedback and Q&A)

---

## 4. Three polish items you can add right after going live

### 1. CI badge (auto-run tests, the badge at the top of README turns green)

Create `.github/workflows/test.yml`:

```yaml
name: Tests

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      - name: Install dependencies
        run: pip install -r requirements.txt
      - name: Run tests
        run: pytest -v
        env:
          LLM_PROVIDER: mock
```

Then add to the top of README:
```markdown
![Tests](https://github.com/<username>/MultiAgentLab/actions/workflows/test.yml/badge.svg)
```

> Note: CI must set `LLM_PROVIDER=mock`, otherwise it will try to call real APIs (real_llm is already skipped by default, this is a double safety).

### 2. First release

On the repo page, right side **Releases** → **Create a new release** → Tag `v0.1.0` → title `v0.1.0 - Initial Release` → paste the feature list from README into the description.

### 3. Real-run screenshot

Take a screenshot of the terminal output of `run_real_demo.py`, save it as `docs/images/real_run_screenshot.png`, then insert into the Real Run Showcase section of README:

```markdown
![Real Run](docs/images/real_run_screenshot.png)
```

> ⚠️ Clear the screen before screenshotting, make sure **no API key is captured**.

---

## 5. Pre-push checklist

- [ ] `.env` is not committed (not visible in `git status`)
- [ ] No API key inside `examples/sample_real_run.json`
- [ ] All tests pass: `pytest` (should be 32 passed)
- [ ] Repo URL / username placeholders in README are replaced
- [ ] Repository is **Public**

---

## 6. 30-second opening pitch (backup)

> "This project tackles the question of 'how well multi-agent systems run, and why they fail'. Existing frameworks like CrewAI and AutoGPT only care about whether tasks complete, but they lack systematic trajectory recording and evaluation. I implemented a closed-loop Planner–Executor–Critic framework that fully records every step's thought/action/observation/token consumption, and verified the end-to-end pipeline with a real DeepSeek API. Next steps include adding LLM-as-Judge automatic evaluation and failure attribution analysis."

---

## 7. Subsequent roadmap (mirrors README)

| Version | Content | Highlight |
|---------|---------|-----------|
| v0.2 | Vue3 + ECharts trajectory timeline visualization | Frontend engineering capability |
| v0.3 | Evaluation metrics + LLM-as-Judge failure attribution | **Core paper novelty** |
| v0.4 | Cross-framework benchmark against CrewAI / AutoGPT | **Paper comparison experiments** |
| v0.5 | Paper draft (EMNLP Findings / ACL Workshop / CCKS) | Research output |