# NewsMemeAI

NewsMemeAI turns RSS/Atom headlines into shareable meme drafts. It is a
stdlib-only Python CLI with an optional OpenAI-compatible caption backend and an
SVG renderer.

## Git workflow

See `docs/git-workflow.md` for the SDLC workflow (topic branches, PRs, no rebase,
SemVer). Short version:

- Branch from `development` as `feature/<topic>`, `fix/<topic>`, etc.
- Open a PR into `development`; promote with a `development` → `main` release PR.
- Never rebase. Use merge commits or plain `git pull`.
- Tag releases on `main` with annotated `vMAJOR.MINOR.PATCH` tags.

Skills are not bundled. Install the optional set with `code-inference --add-skills`.

## Commands

| Action | Command |
|--------|---------|
| Install | `pip install -e .` |
| Install dev dependencies | `pip install -r dev-requirements.txt` |
| Install pre-commit hooks | `pre-commit install` |
| Lint | `ruff check .` |
| Format | `ruff format .` |
| Format check | `ruff format --check .` |
| Type check | `mypy src/` |
| Run tests | `pytest -v` |
| Run the CLI | `newsmemeai --help` |

## Conventions

- Python 3.11+ with `from __future__ import annotations`; type hints on every
  public function.
- `src/` layout; runtime code must not import third-party packages. Add a new
  dependency only with an ADR in `docs/adr/`.
- Ruff and mypy strict are the source of truth for style and types.
- Tests use pytest and local XML fixtures; no test may require network access.
- Treat feed content as untrusted. Escape it before it reaches SVG, JSON, or a
  shell.
- Keep commits focused. Describe behaviour, not file names.
- Public behaviour changes need a README or docs update in the same PR.
