"""End-to-end CLI tests using local feed fixtures."""

from __future__ import annotations

import json
from pathlib import Path

from newsmemeai.cli import main

RSS = """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <title>Fixture News</title>
    <item>
      <title>Robots learn to garden</title>
      <link>https://example.com/garden</link>
      <pubDate>Sun, 16 Nov 2026 09:00:00 GMT</pubDate>
      <description>Tomatoes are involved.</description>
    </item>
    <item>
      <title>Moon gets a new parking lot</title>
      <link>https://example.com/moon</link>
    </item>
  </channel>
</rss>
"""


def _feed(tmp_path: Path) -> Path:
    feed = tmp_path / "fixture.xml"
    feed.write_text(RSS, encoding="utf-8")
    return feed


def test_headlines_json(tmp_path: Path, capsys) -> None:
    exit_code = main(["headlines", "--feed", str(_feed(tmp_path)), "--json"])
    assert exit_code == 0
    payload = json.loads(capsys.readouterr().out)
    assert [headline["title"] for headline in payload] == [
        "Robots learn to garden",
        "Moon gets a new parking lot",
    ]


def test_headlines_human_output(tmp_path: Path, capsys) -> None:
    exit_code = main(["headlines", "--feed", str(_feed(tmp_path))])
    assert exit_code == 0
    output = capsys.readouterr().out
    assert "1. Robots learn to garden" in output
    assert "2. Moon gets a new parking lot" in output


def test_generate_writes_svg(tmp_path: Path, capsys) -> None:
    destination = tmp_path / "meme.svg"
    exit_code = main(
        [
            "generate",
            "--feed",
            str(_feed(tmp_path)),
            "--index",
            "2",
            "--no-llm",
            "--out",
            str(destination),
        ]
    )
    assert exit_code == 0
    assert destination.exists()
    assert "Moon gets a new parking lot" in destination.read_text(encoding="utf-8")
    assert f"Wrote {destination}" in capsys.readouterr().out


def test_generate_manual_caption(tmp_path: Path, capsys) -> None:
    destination = tmp_path / "manual.svg"
    exit_code = main(
        [
            "generate",
            "--feed",
            str(_feed(tmp_path)),
            "--top",
            "ME:",
            "--bottom",
            "READING THE NEWS",
            "--out",
            str(destination),
        ]
    )
    assert exit_code == 0
    svg = destination.read_text(encoding="utf-8")
    assert "ME:" in svg
    assert "READING THE NEWS" in svg


def test_generate_json_metadata(tmp_path: Path, capsys) -> None:
    exit_code = main(
        [
            "generate",
            "--feed",
            str(_feed(tmp_path)),
            "--no-llm",
            "--out",
            str(tmp_path / "meta.svg"),
            "--json",
        ]
    )
    assert exit_code == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["headline"]["title"] == "Robots learn to garden"
    assert payload["caption"]["model"] == "template"


def test_generate_index_out_of_range(tmp_path: Path, capsys) -> None:
    exit_code = main(["generate", "--feed", str(_feed(tmp_path)), "--index", "99", "--no-llm"])
    assert exit_code == 1
    assert "out of range" in capsys.readouterr().err


def test_missing_feed(tmp_path: Path, capsys) -> None:
    exit_code = main(["headlines", "--feed", str(tmp_path / "missing.xml")])
    assert exit_code == 1
    assert "could not read feed" in capsys.readouterr().err
