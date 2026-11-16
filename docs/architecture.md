# Architecture

## Goals

- Turn one news item into a caption and a self-contained SVG with one command.
- Keep the runtime core dependency-free, deterministic, and easy to audit.
- Allow an AI caption provider without making it a hard requirement.
- Never execute or trust feed content.

## Non-goals

- Hosting a web service, scheduler, or social-media publisher.
- Fact-checking or summarising the news.
- Ranking headlines by virality across a large corpus.
- Pixel-perfect PNG rendering in the core package.

## Context

```text
                 ┌────────────────────────────────────────────┐
  RSS / Atom ───▶│ feeds.py                                   │
                 │ fetch → parse → clean → dedupe             │
                 └──────────────────┬─────────────────────────┘
                                    │ list[Headline]
                                    ▼
                 ┌────────────────────────────────────────────┐
                 │ captions.py                                │
                 │ template (default)  or  chat completions   │
                 │ prompt → JSON → validation                 │
                 └──────────────────┬─────────────────────────┘
                                    │ Caption
                                    ▼
                 ┌────────────────────────────────────────────┐
                 │ render.py                                  │
                 │ wrap → escape → layout → write SVG          │
                 └──────────────────┬─────────────────────────┘
                                    │
                                    ▼
                                meme.svg
```

The CLI (`cli.py`) composes the three stages and owns user-facing error messages.
Every stage is importable on its own.

## Data contracts

### `Headline`

| Field | Type | Notes |
| --- | --- | --- |
| `title` | `str` | Required; blank items are dropped |
| `link` | `str` | Empty when the feed has no link |
| `source` | `str` | URL or path passed to `--feed` |
| `published` | `str` | Raw feed timestamp; no date parsing |
| `summary` | `str` | HTML stripped and entities decoded |

Headlines are deduplicated by case-folded title, first occurrence wins.

### `Caption`

| Field | Type | Notes |
| --- | --- | --- |
| `top` | `str` | May be empty |
| `bottom` | `str` | May be empty; not both |
| `rationale` | `str` | Template explanation or model rationale |
| `model` | `str` | `template`, `manual`, or the configured model name |

### `LLMConfig`

Built from `NEWSMEMEAI_BASE_URL`, `NEWSMEMEAI_MODEL`, `NEWSMEMEAI_API_KEY`, and
`NEWSMEMEAI_TIMEOUT`. The config is present only when both the base URL and model are
set.

## Behaviour and failure modes

| Condition | Behaviour |
| --- | --- |
| Feed is unreachable or unreadable | `FeedError`; CLI exits 1 with the source in the message |
| XML is malformed | `FeedError` with the parser position |
| Document is neither RSS nor Atom | `FeedError` naming the root element |
| Feed has zero valid items | Empty list; CLI reports "no headlines found" |
| No AI configured | Deterministic template caption |
| AI endpoint returns HTTP error / is unreachable | `ModelError`; CLI exits 1 |
| AI returns invalid JSON or no text | `CaptionError`; CLI exits 1 |
| `--index` exceeds the collected headlines | `CaptionError`; CLI exits 1 |
| SVG output directory is missing | Created before writing |

There is no silent AI fallback. A failed AI call is visible; `--no-llm` is the explicit
opt-out.

## Security and privacy

- Feed titles and summaries are untrusted. They are stripped of HTML, passed as data
  to the model, and XML-escaped before rendering.
- The prompt instructs the model to ignore instructions embedded in the headline.
- API keys come from the environment and are only used in an `Authorization` header.
- No telemetry, no analytics, no outbound calls except the feeds and the explicitly
  configured model endpoint.
- SVG is text. Do not render untrusted SVG from other sources in the same context
  without sanitising it.

## Determinism

`template_caption` hashes the case-folded headline with SHA-256 and uses the first byte
to select from a fixed template list. The same headline and style always produce the
same caption, which keeps tests and demos stable.

The AI path is intentionally non-deterministic; callers that need reproducibility
should use `--no-llm`.

## Extension points

- **New feed format** — extend `parse_feed`; keep the `Headline` contract.
- **New caption provider** — implement a function with the `_chat` shape and return
  text; `generate_caption` owns validation.
- **New renderer** — add a module that consumes `Caption`; do not leak rendering
  concerns into `captions.py`.
- **PNG output** — add an optional extra rather than a runtime dependency, and convert
  the SVG with a tool such as `cairosvg` or `resvg`.

## Testing strategy

- Unit tests cover parsing, cleaning, template determinism, response validation,
  wrapping, escaping, and file output.
- CLI tests use local XML files and `--no-llm`; the suite never touches the network.
- CI runs ruff, ruff format check, mypy strict, and pytest on Python 3.11–3.13.
