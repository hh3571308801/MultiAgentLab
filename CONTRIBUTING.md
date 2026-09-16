# Contributing to Open

First off, thanks for taking the time to contribute! 🎉

This project is an open-source multi-agent collaboration framework, and any kind of contribution — bug reports, feature requests, doc fixes, code patches — is welcome and appreciated.

---

## Quick links

- 🐛 [Report a bug](https://github.com/hh3571308801/MultiAgentLab/issues/new?template=bug.md)
- 💡 [Request a feature](https://github.com/hh3571308801/MultiAgentLab/issues/new?template=feature.md)
- ❓ [Ask a question](https://github.com/hh3571308801/MultiAgentLab/discussions)
- 📖 [Read the architecture doc](docs/architecture.md)

---

## 🛠 Development setup

```bash
# 1. Fork and clone the repo
git clone https://github.com/<your-username>/MultiAgentLab.git
cd MultiAgentLab

# 2. Create a virtual environment (Python 3.10+)
python -m venv .venv
source .venv/bin/activate        # Linux / macOS
.venv\Scripts\activate           # Windows

# 3. Install dependencies (including dev tools)
pip install -r requirements.txt
pip install pytest pytest-asyncio httpx ruff mypy

# 4. Copy env file (use mock mode for local dev)
cp .env.example .env
# keep LLM_PROVIDER=mock in .env

# 5. Run the test suite — should report "33 passed"
pytest
```

---

## 📋 Contribution workflow

1. **Create an issue first** (for non-trivial changes). Discuss the design before writing code.
2. **Fork the repo** and create a topic branch:
   ```bash
   git checkout -b feat/add-search-tool        # new feature
   git checkout -b fix/executor-json-parse     # bug fix
   git checkout -b docs/improve-architecture   # docs only
   ```
3. **Write code + tests**. New code should be covered by tests under `tests/`.
4. **Run the full test suite locally** before pushing:
   ```bash
   pytest
   ruff check backend/ tests/
   ```
5. **Commit using [Conventional Commits](https://www.conventionalcommits.org/)**:
   ```
   feat: add web search tool
   fix: planner crashes on empty plan
   docs: clarify trajectory schema in architecture.md
   test: cover calculator overflow edge case
   refactor: extract retry logic into shared helper
   ```
6. **Push and open a Pull Request** against `main`. Fill in the PR template — link the related issue, describe the change, and add screenshots if relevant.
7. **Wait for CI**. The test workflow must turn green before review. PRs without green CI will not be merged.

---

## 📐 Code conventions

| Aspect | Rule |
|--------|------|
| Style | PEP 8, enforced via `ruff check` |
| Type hints | Required for all new public functions |
| Docstrings | Google-style, required for all public modules / classes / functions |
| Logging | Use `logging.getLogger(__name__)`, never `print()` in library code |
| Imports | Absolute imports only, sorted by `ruff` |
| Line length | 100 characters max |
| Async | `async def` for any I/O-bound function (LLM calls, tool calls) |

Example function:

```python
async def execute_tool(name: str, args: dict[str, Any]) -> ToolResult:
    """Run a registered tool and capture its output.

    Args:
        name: Registered tool name (e.g. "calculator").
        args: Arguments passed to the tool.

    Returns:
        A ToolResult with the raw output and any error info.

    Raises:
        ToolNotFoundError: If the tool name is not registered.
    """
    ...
```

---

## 🧪 Testing conventions

- All tests live under `tests/` and use `pytest`.
- Use `pytest.mark.asyncio` for async test functions.
- Use `httpx.AsyncClient` to exercise FastAPI endpoints.
- Real LLM calls are gated by `@pytest.mark.real_llm` and **skipped by default** — `pytest.ini` sets `addopts = -m "not real_llm"`.
- Aim for >80% coverage on new code (`pytest --cov=backend`).
- A new feature without tests will not be merged.

---

## 📂 Where to put your code

| You are adding... | Put it in... | Then... |
|--------------------|--------------|---------|
| A new Agent role | `backend/agents/<role>.py` | Register in `backend/agents/__init__.py` |
| A new tool | `backend/tools/<tool>.py` | Register in `backend/tools/registry.py` |
| A new LLM provider | `backend/llm/client.py` | Add a branch in `_call_provider()` |
| A new API route | `backend/api/routes.py` | Update `docs/architecture.md` |
| A new evaluation metric | `backend/evaluation/<metric>.py` | Wire into `EvaluationRunner` |
| Docs / tutorials | `docs/<topic>.md` | Link from README if relevant |

---

## 🚫 What we don't accept

- Changes that break the public trajectory schema without a migration plan
- New dependencies that bloat the install footprint without clear value
- Code without tests
- Large refactors without an agreed-upon design discussion
- Anything that touches user data outside the project directory

---

## 🤝 Code of conduct

Be kind, be respectful. We follow the standard open-source etiquette:

- Assume good faith. Ask before judging.
- Critique ideas, not people.
- Help newcomers — everyone started from zero once.
- No harassment, no discrimination, no bad-faith behavior.

If you experience or witness a violation, reach out via GitHub Issues (private contact info is not required).

---

## 📜 License

By contributing, you agree that your contributions will be licensed under the [MIT License](LICENSE).

---

## 💬 Questions?

Open a [Discussion](https://github.com/hh3571308801/MultiAgentLab/discussions) — that's the fastest way to get help without filing a formal issue.

Thanks again for contributing! 🚀