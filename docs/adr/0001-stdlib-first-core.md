# ADR 0001: Stdlib-first core

- **Status:** Accepted
- **Date:** 2026-11-16
- **Deciders:** NewsMemeAI maintainers

## Context

The first release needs to fetch feeds, call an optional chat API, and write an image.
The obvious stack is `feedparser` + `requests` + `Pillow`, which is convenient but
brings a large dependency surface for three small jobs. The tool should run in a cron
job, a GitHub Action, or a laptop with no virtualenv-friendly network access.

## Decision

The runtime package depends only on the Python standard library (Python 3.11+).

- `urllib.request` for HTTP.
- `xml.etree.ElementTree` for RSS and Atom.
- `json` and `hashlib` for captions and deterministic template selection.
- A hand-written SVG renderer instead of an image library.

Optional developer tools and future renderers live in extras, never in `dependencies`.

## Consequences

Positive:

- `pip install newsmemeai` is fast and has no supply-chain surface beyond the package.
- Feed parsing and escaping are visible in one small module.
- SVG output is crisp, diffable, and requires no native libraries.

Negative:

- We own the feed edge cases (namespaces, malformed XML, HTML summaries).
- No PNG in the core; users need an external converter for raster output.
- `xml.etree` is not hardened against every entity-expansion attack. We only fetch
  feeds from URLs the user chooses and do not process arbitrary uploads.

## Revisit when

- Feed compatibility becomes a recurring bug source.
- PNG output becomes the primary use case rather than an export step.
- A dependency already present in the deployment environment can replace a module
  without increasing the install surface.
