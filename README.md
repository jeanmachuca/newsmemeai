# NewsMemeAI

**Turn the day's headlines into shareable meme drafts.**

NewsMemeAI reads RSS/Atom feeds, picks a headline, writes a caption, and renders a
1080 × 1080 SVG poster that is ready to post or convert to PNG.

[![CI](https://github.com/jeanmachuca/newsmemeai/actions/workflows/ci.yml/badge.svg)](https://github.com/jeanmachuca/newsmemeai/actions/workflows/ci.yml)

- **Zero runtime dependencies** — the core uses only the Python standard library.
- **Works offline** — a deterministic template generator is the default caption path.
- **Optional AI captions** — connect any OpenAI-compatible chat endpoint.
- **Safe rendering** — untrusted headlines are escaped before they enter the SVG.

## Quick start

```bash
git clone git@github.com:jeanmachuca/newsmemeai.git
cd newsmemeai

python3 -m venv .venv
source .venv/bin/activate
pip install -e .
pip install -r dev-requirements.txt

newsmemeai --version
newsmemeai headlines --limit 3
newsmemeai generate --index 1 --out out/meme.svg
```

Open `out/meme.svg` in a browser, or convert it with your favourite image tool.

## Commands

### List headlines

```bash
newsmemeai headlines
newsmemeai headlines --feed https://hnrss.org/frontpage --limit 5
newsmemeai headlines --json
```

### Generate a meme

```bash
# First headline from the default feeds, deterministic caption
newsmemeai generate --no-llm --out out/meme.svg

# Pick another headline and a style
newsmemeai generate --index 3 --style reaction --out out/reaction.svg

# Use your own words
newsmemeai generate --top "ME:" --bottom "READING THE NEWS" --out out/manual.svg
```

Styles: `classic`, `reaction`, `headline`.

### Local feeds

`--feed` accepts an HTTP(S) URL or a local path, so you can iterate without the network:

```bash
newsmemeai headlines --feed tests/fixtures/news.xml
```

## AI captions

Set an OpenAI-compatible base URL and model. The key is optional for local servers.

```bash
export NEWSMEMEAI_BASE_URL=http://localhost:11434/v1
export NEWSMEMEAI_MODEL=llama3.2
# export NEWSMEMEAI_API_KEY=...        # only if your endpoint requires it
# export NEWSMEMEAI_TIMEOUT=30         # seconds

newsmemeai generate --out out/ai.svg
```

| Variable | Required | Meaning |
| --- | --- | --- |
| `NEWSMEMEAI_BASE_URL` | for AI captions | Base URL of the chat API, e.g. `http://localhost:11434/v1` |
| `NEWSMEMEAI_MODEL` | for AI captions | Model name sent in the request |
| `NEWSMEMEAI_API_KEY` | no | Bearer token for hosted endpoints |
| `NEWSMEMEAI_TIMEOUT` | no | Request timeout in seconds (default `30`) |

If the variables are unset, NewsMemeAI uses the template generator. If the endpoint
fails, the command exits with an error instead of silently inventing a caption; add
`--no-llm` to force the deterministic path. Credentials are read from the environment
and are never written to disk.

## How it works

```text
RSS / Atom ──▶ feeds.py ──▶ captions.py ──▶ render.py ──▶ .svg
                parse        template or LLM    escaped poster
```

| Module | Responsibility |
| --- | --- |
| `feeds.py` | Fetch and parse RSS 2.0 / Atom into `Headline` records |
| `captions.py` | Deterministic templates, prompt construction, model client, JSON parsing |
| `render.py` | Word wrapping, XML escaping, 1080 × 1080 SVG layout |
| `cli.py` | `headlines` and `generate` commands |

The design favours a small, auditable core over a framework. See
[`docs/architecture.md`](docs/architecture.md) for data contracts and failure modes,
and [`docs/adr/0001-stdlib-first-core.md`](docs/adr/0001-stdlib-first-core.md) for the
reasoning behind the zero-dependency rule.

## Project layout

```text
.
├── src/newsmemeai/      # package
├── tests/               # pytest suite, local feed fixtures
├── docs/                # architecture, ADRs, git workflow
├── .github/workflows/   # CI and PR automation
├── AGENTS.md            # instructions for AI coding agents
└── pyproject.toml       # packaging, ruff, mypy, pytest
```

## Development

| Action | Command |
| --- | --- |
| Install | `pip install -e .` |
| Dev tools | `pip install -r dev-requirements.txt` |
| Hooks | `pre-commit install` |
| Lint | `ruff check .` |
| Format | `ruff format .` |
| Format check | `ruff format --check .` |
| Types | `mypy src/` |
| Tests | `pytest -v` |

## Git workflow

Work happens on a topic branch from `development`, lands through a PR, and is promoted
to `main` with a release PR. No rebasing. Releases use annotated SemVer tags. The full
rules live in [`docs/git-workflow.md`](docs/git-workflow.md).

## License

MIT © 2026 Jean Machuca
