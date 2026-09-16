# 发布到 GitHub 指南

> 本地仓库已就绪（`main` 分支，首次提交已完成）。以下是把它推上 GitHub 的完整步骤。

---

## 一、创建远程仓库（2 分钟）

1. 打开 https://github.com/new
2. 填写：

| 字段 | 填什么 |
|------|--------|
| **Repository name** | `MultiAgentLab` |
| **Description** | `An observable & evaluable multi-LLM-agent collaboration framework with full trajectory recording` |
| **Visibility** | ✅ **Public**（面试官要看，必须公开）|
| **Initialize this repository with** | ❌ **全部不勾**（README / .gitignore / license 都不要勾，否则会和本地冲突）|

3. 点 **Create repository**

---

## 二、推送到 GitHub（1 分钟）

创建后会看到一页命令提示，**只用看 "…or push an existing repository" 那一段**：

```bash
cd C:\Users\35713\Desktop\MultiAgentLab

# 把 <你的GitHub用户名> 换成实际的（本机 git 配置是 hh3571308801）
git remote add origin https://github.com/<你的GitHub用户名>/MultiAgentLab.git

git branch -M main
git push -u origin main
```

推送时会弹出登录窗口（浏览器授权或用 Personal Access Token）。
**首次推送到 GitHub 需要 PAT**，如果没配过：
GitHub → 右上角头像 → Settings → Developer settings → Personal access tokens → Tokens (classic) → Generate new token → 勾选 `repo` 权限 → 复制，粘贴到密码框。

---

## 三、仓库设置（让项目"看起来专业"，5 分钟）

推到 GitHub 后，进仓库页面右上角 **⚙️ Settings** 旁边的 **About**（铅笔图标），填：

**Description**：
```
An observable & evaluable multi-LLM-agent collaboration framework with full trajectory recording.
Planner → Executor → Critic loop | Multi-provider (DeepSeek/OpenAI/Qwen) | FastAPI | 33 tests
```

**Topics**（逐个添加，共 8 个）：
```
llm  agent  multi-agent  llm-agent  trajectory  evaluation  fastapi  python
```

**勾选**：
- ☑️ Releases
- ☑️ Packages（可选）
- ☑️ Discussions（**建议开**，面试时可以说"社区有人来讨论过"）

---

## 四、上线后立刻能加的 3 个加分项

### 1. CI 徽章（自动跑测试，README 顶部会亮绿标）

新建 `.github/workflows/test.yml`：

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

然后在 README 顶部加：

```markdown
![Tests](https://github.com/<用户名>/MultiAgentLab/actions/workflows/test.yml/badge.svg)
```

> 注意：CI 里必须设 `LLM_PROVIDER=mock`，否则会尝试调真实 API（虽然默认已跳过 `real_llm`，双保险）。

### 2. 第一次 Release

仓库页面右侧 **Releases** → **Create a new release** → Tag 填 `v0.1.0` → 标题 `v0.1.0 - Initial Release` → 描述里粘贴 README 的功能列表。

### 3. 真实运行截图

把终端跑 `run_real_demo.py` 的输出截图，存到 `docs/images/real_run_screenshot.png`，然后在 README 的 Real Run Showcase 章节插入：

```markdown
![Real Run](docs/images/real_run_screenshot.png)
```

> ⚠️ 截图前先清屏，确保**不要截到 API Key**。

---

## 五、推送前的自检清单

- [ ] `.env` 没有被提交（`git status` 里看不到它）
- [ ] `examples/sample_real_run.json` 里没有 API Key
- [ ] 所有测试通过：`pytest`（应为 32 passed）
- [ ] README 里的仓库链接/用户名如果是占位符，已替换
- [ ] 仓库是 **Public**

---

## 六、面试时的 30 秒开场（备用）

> "这个项目解决的是多 Agent 系统'跑得好不好、为什么失败'的问题。现有框架如 CrewAI、AutoGPT 只关注能否跑通，但缺乏系统化的轨迹记录与评测。我实现了一个 Planner-Executor-Critic 三角色闭环框架，完整记录每一步的 thought/action/observation/token 消耗，并用真实 DeepSeek API 验证了端到端链路。下一步计划加入 LLM-as-Judge 自动评测和失败归因分析。"

---

## 七、后续路线图（对应 README）

| 版本 | 内容 | 面试价值 |
|------|------|---------|
| v0.2 | Vue3 + ECharts 轨迹时间线可视化 | 展示前端工程能力 |
| v0.3 | 评测指标 + LLM-as-Judge 失败归因 | **论文核心创新点** |
| v0.4 | 与 CrewAI / AutoGPT 横向 benchmark | **论文对比实验** |
| v0.5 | 论文初稿（EMNLP Findings / ACL Workshop / CCKS）| 研究成果 |
