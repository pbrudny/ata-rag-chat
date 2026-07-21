import re
from dataclasses import dataclass

import tiktoken

MIN_TOKENS = 700
MAX_TOKENS = 900
OVERLAP_TOKENS = 100

_HEADING_RE = re.compile(r"^(#{1,4})\s+(.*)$")
_ENCODING = tiktoken.get_encoding("cl100k_base")


def count_tokens(text: str) -> int:
    return len(_ENCODING.encode(text))


@dataclass(frozen=True)
class Chunk:
    section: str
    text: str
    token_count: int


@dataclass(frozen=True)
class _Section:
    breadcrumb: str
    parent_breadcrumb: str
    text: str


def chunk_markdown(markdown: str) -> list[Chunk]:
    """Heading-aware chunking: sections within 700-900 tokens become a single
    chunk, smaller sections merge with the next sibling under the same parent
    heading, larger sections split with a sliding window (paragraph, then
    sentence boundaries) with a 100-token overlap."""
    sections = _split_into_sections(markdown)
    merged_sections = _merge_small_sections(sections)

    chunks: list[Chunk] = []
    for section in merged_sections:
        token_count = count_tokens(section.text)
        if token_count <= MAX_TOKENS:
            chunks.append(
                Chunk(section=section.breadcrumb, text=section.text, token_count=token_count)
            )
        else:
            chunks.extend(_split_oversized_section(section))
    return chunks


def _split_into_sections(markdown: str) -> list[_Section]:
    stack: list[tuple[int, str]] = []
    sections: list[_Section] = []
    current_lines: list[str] = []

    def breadcrumb_of(stack_slice: list[tuple[int, str]]) -> str:
        return " > ".join(title for _, title in stack_slice)

    def flush() -> None:
        text = "\n".join(current_lines).strip()
        if text:
            sections.append(
                _Section(
                    breadcrumb=breadcrumb_of(stack),
                    parent_breadcrumb=breadcrumb_of(stack[:-1]),
                    text=text,
                )
            )
        current_lines.clear()

    for line in markdown.splitlines():
        match = _HEADING_RE.match(line)
        if match:
            flush()
            level = len(match.group(1))
            title = match.group(2).strip()
            while stack and stack[-1][0] >= level:
                stack.pop()
            stack.append((level, title))
        current_lines.append(line)
    flush()

    return sections


def _merge_small_sections(sections: list[_Section]) -> list[_Section]:
    merged: list[_Section] = []
    buffer: _Section | None = None

    for section in sections:
        if buffer is None:
            buffer = section
            continue
        same_parent = buffer.parent_breadcrumb == section.parent_breadcrumb
        if count_tokens(buffer.text) < MIN_TOKENS and same_parent:
            buffer = _Section(
                breadcrumb=buffer.breadcrumb,
                parent_breadcrumb=buffer.parent_breadcrumb,
                text=buffer.text + "\n\n" + section.text,
            )
        else:
            merged.append(buffer)
            buffer = section
    if buffer is not None:
        merged.append(buffer)
    return merged


def _split_into_paragraphs(text: str) -> list[str]:
    return [p for p in re.split(r"\n\s*\n", text) if p.strip()]


def _split_into_sentences(text: str) -> list[str]:
    sentences = re.split(r"(?<=[.!?])\s+", text.strip())
    return [s for s in sentences if s.strip()]


def _atomize(paragraphs: list[str]) -> list[str]:
    units: list[str] = []
    for paragraph in paragraphs:
        if count_tokens(paragraph) > MAX_TOKENS:
            units.extend(_split_into_sentences(paragraph))
        else:
            units.append(paragraph)
    return units


def _split_oversized_section(section: _Section) -> list[Chunk]:
    units = _atomize(_split_into_paragraphs(section.text))
    return _pack_units(units, section.breadcrumb)


def _pack_units(units: list[str], breadcrumb: str) -> list[Chunk]:
    chunks: list[Chunk] = []
    current: list[str] = []
    current_tokens = 0

    for unit in units:
        unit_tokens = count_tokens(unit)
        if current and current_tokens + unit_tokens > MAX_TOKENS:
            chunks.append(_make_chunk(breadcrumb, current, current_tokens))
            current, current_tokens = _seed_overlap(current)
        current.append(unit)
        current_tokens += unit_tokens

    if current:
        chunks.append(_make_chunk(breadcrumb, current, current_tokens))

    return chunks


def _make_chunk(breadcrumb: str, units: list[str], token_count: int) -> Chunk:
    return Chunk(section=breadcrumb, text="\n\n".join(units), token_count=token_count)


def _seed_overlap(units: list[str]) -> tuple[list[str], int]:
    seed: list[str] = []
    seed_tokens = 0
    for unit in reversed(units):
        unit_tokens = count_tokens(unit)
        if seed and seed_tokens + unit_tokens > OVERLAP_TOKENS:
            break
        seed.insert(0, unit)
        seed_tokens += unit_tokens
    return seed, seed_tokens
