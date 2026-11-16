"""Command-line entry point for NewsMemeAI."""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence
from dataclasses import asdict

from . import __version__
from .captions import (
    STYLES,
    Caption,
    CaptionError,
    ModelError,
    generate_caption,
    template_caption,
)
from .feeds import FeedError, Headline, collect_headlines
from .render import write_svg

DEFAULT_FEEDS = (
    "https://feeds.bbci.co.uk/news/rss.xml",
    "https://www.theverge.com/rss/index.xml",
)


def _positive_int(value: str) -> int:
    try:
        parsed = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("must be an integer") from exc
    if parsed < 1:
        raise argparse.ArgumentTypeError("must be at least 1")
    return parsed


def _positive_float(value: str) -> float:
    try:
        parsed = float(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("must be a number") from exc
    if parsed <= 0:
        raise argparse.ArgumentTypeError("must be greater than zero")
    return parsed


def _add_feed_options(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--feed",
        action="append",
        dest="feeds",
        metavar="URL_OR_PATH",
        help="RSS/Atom URL or local file; repeat for multiple feeds",
    )
    parser.add_argument(
        "--limit",
        type=_positive_int,
        default=5,
        metavar="N",
        help="headlines per feed (default: 5)",
    )
    parser.add_argument(
        "--timeout",
        type=_positive_float,
        default=10.0,
        metavar="SECONDS",
        help="network timeout (default: 10)",
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="newsmemeai",
        description="Turn the day's headlines into shareable meme drafts.",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    subparsers = parser.add_subparsers(dest="command", required=True)

    headlines = subparsers.add_parser("headlines", help="list the latest headlines")
    _add_feed_options(headlines)
    headlines.add_argument("--json", action="store_true", help="emit JSON")

    generate = subparsers.add_parser("generate", help="render one headline as a meme")
    _add_feed_options(generate)
    generate.add_argument(
        "--index",
        type=_positive_int,
        default=1,
        metavar="N",
        help="1-based headline to use (default: 1)",
    )
    generate.add_argument(
        "--style",
        choices=STYLES,
        default="classic",
        help="caption style (default: classic)",
    )
    generate.add_argument(
        "--out",
        default="meme.svg",
        metavar="PATH",
        help="output SVG path (default: meme.svg)",
    )
    generate.add_argument(
        "--no-llm",
        action="store_true",
        help="use the deterministic template even when a model is configured",
    )
    generate.add_argument("--top", help="override the top caption")
    generate.add_argument("--bottom", help="override the bottom caption")
    generate.add_argument("--json", action="store_true", help="emit JSON metadata")

    return parser


def _sources(args: argparse.Namespace) -> list[str]:
    return list(args.feeds) if args.feeds else list(DEFAULT_FEEDS)


def _cmd_headlines(args: argparse.Namespace) -> int:
    headlines = collect_headlines(
        _sources(args),
        limit_per_feed=args.limit,
        timeout=args.timeout,
    )
    if args.json:
        payload = [asdict(headline) for headline in headlines]
        print(json.dumps(payload, indent=2, ensure_ascii=False))
        return 0
    if not headlines:
        print("newsmemeai: no headlines found", file=sys.stderr)
        return 1

    for index, headline in enumerate(headlines, start=1):
        print(f"{index:2}. {headline.title}")
        details = headline.source
        if headline.published:
            details = f"{details} · {headline.published}"
        print(f"    {details}")
    return 0


def _caption_for(args: argparse.Namespace, headline: Headline) -> Caption:
    if args.top is not None or args.bottom is not None:
        caption = Caption(
            top=args.top or "",
            bottom=args.bottom or "",
            rationale="Manual override.",
            model="manual",
        )
        if not caption.as_text():
            raise CaptionError("--top and --bottom cannot both be empty")
        return caption
    if args.no_llm:
        return template_caption(headline.title, style=args.style)
    return generate_caption(headline.title, style=args.style)


def _cmd_generate(args: argparse.Namespace) -> int:
    headlines = collect_headlines(
        _sources(args),
        limit_per_feed=args.limit,
        timeout=args.timeout,
    )
    if not headlines:
        print("newsmemeai: no headlines found", file=sys.stderr)
        return 1
    if args.index > len(headlines):
        raise CaptionError(f"--index {args.index} is out of range (found {len(headlines)})")

    headline = headlines[args.index - 1]
    caption = _caption_for(args, headline)
    destination = write_svg(args.out, caption, source=headline.source)

    if args.json:
        print(
            json.dumps(
                {
                    "path": str(destination),
                    "headline": asdict(headline),
                    "caption": asdict(caption),
                },
                indent=2,
                ensure_ascii=False,
            )
        )
        return 0

    print(f"Wrote {destination}")
    print(f"Headline: {headline.title}")
    print()
    print(caption.as_text())
    if caption.rationale:
        print(f"\n({caption.rationale})")
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        if args.command == "headlines":
            return _cmd_headlines(args)
        return _cmd_generate(args)
    except (FeedError, CaptionError, ModelError, OSError, ValueError) as exc:
        print(f"newsmemeai: error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
