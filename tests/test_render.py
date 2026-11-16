"""SVG wrapping, escaping, and file-writing tests."""

from __future__ import annotations

from newsmemeai.captions import Caption
from newsmemeai.render import render_svg, wrap_text, write_svg


def test_wrap_text_on_words() -> None:
    assert wrap_text("one two three four", max_chars=7) == ["one two", "three", "four"]


def test_wrap_text_preserves_explicit_lines() -> None:
    assert wrap_text("first line\nsecond line", max_chars=20) == ["first line", "second line"]


def test_wrap_text_hard_breaks_long_words() -> None:
    assert wrap_text("abcdefghij", max_chars=4) == ["abcd", "efgh", "ij"]


def test_wrap_text_empty() -> None:
    assert wrap_text("") == []


def test_render_escapes_text_and_metadata() -> None:
    caption = Caption(top="<script>alert(1)</script>", bottom="A & B")
    svg = render_svg(caption, source="https://example.com/?a=1&b=2")
    assert "<script>" not in svg
    assert "&lt;script&gt;" in svg
    assert "A &amp; B" in svg
    assert "https://example.com/?a=1&amp;b=2" in svg
    assert 'width="1080"' in svg
    assert 'height="1080"' in svg


def test_render_includes_both_caption_blocks() -> None:
    svg = render_svg(Caption(top="TOP LINE", bottom="BOTTOM LINE"))
    assert "TOP LINE" in svg
    assert "BOTTOM LINE" in svg
    assert svg.count("<text") >= 2


def test_write_svg_creates_parent_directory(tmp_path) -> None:
    destination = tmp_path / "nested" / "meme.svg"
    written = write_svg(destination, Caption(top="TOP", bottom="BOTTOM"))
    assert written == destination
    assert destination.read_text(encoding="utf-8").startswith("<svg")
