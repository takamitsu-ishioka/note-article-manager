#!/usr/bin/env python3
"""Extract glossary candidates from a Japanese Markdown article.

Candidate discovery is deterministic. Sudachi supplies Japanese word boundaries
and ``wordfreq`` supplies a general-language frequency estimate. The output is
intended for review; definitions are deliberately left to a later step.
"""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from dataclasses import dataclass
from functools import lru_cache
import json
import math
from pathlib import Path
import re
import sys
from typing import Iterable

try:
    from sudachipy import dictionary, tokenizer
    from wordfreq import get_frequency_dict
except ImportError as exc:  # pragma: no cover - exercised through the CLI
    print(
        "依存ライブラリがありません。次を実行してください:\n"
        "  python3 -m pip install -r requirements-glossary.txt",
        file=sys.stderr,
    )
    raise SystemExit(2) from exc


SCHEMA_VERSION = 1
DEFAULT_LIMIT = 50
DEFAULT_THRESHOLD = 4.0
MAX_ZIPF = 8.0

FENCE_RE = re.compile(r"^\s*(```|~~~)")
HTML_RE = re.compile(r"<[^>]+>")
IMAGE_RE = re.compile(r"!\[[^]]*]\([^)]*\)")
LINK_RE = re.compile(r"\[([^]]+)]\([^)]*\)")
URL_RE = re.compile(r"https?://\S+")
INLINE_CODE_RE = re.compile(r"`[^`]+`")
MARKUP_RE = re.compile(r"[*_#>`~|]+")
ASCII_TERM_RE = re.compile(
    r"(?<![A-Za-z0-9])(?:[A-Za-z][A-Za-z0-9]*(?:[-_.+][A-Za-z0-9]+)*)(?![A-Za-z0-9])"
)
HIRAGANA_RE = re.compile(r"^[ぁ-ゖー]+$")
NUMBER_RE = re.compile(r"^[\d.,]+$")

# Function words and article-writing vocabulary that otherwise score highly
# because short Japanese tokens have unreliable corpus-frequency estimates.
STOPWORDS = {
    "これ", "それ", "あれ", "ここ", "そこ", "ため", "もの", "こと", "とき",
    "よう", "そう", "どこ", "なぜ", "何", "私", "今回", "以前", "最近", "実際",
    "問題", "必要", "状態", "方法", "意味", "説明", "記事", "文章", "仕事", "自分",
    "一つ", "最後", "途中", "現在", "未来", "結果", "場合", "可能", "本来",
}


@dataclass(frozen=True)
class Occurrence:
    term: str
    normalized: str
    line: int
    context: str
    kind: str
    is_unknown: bool = False


def is_noun(morpheme) -> bool:
    return morpheme.part_of_speech()[0] == "名詞"


def visible_lines(markdown: str) -> Iterable[tuple[int, str]]:
    """Yield visible prose, excluding fenced code and Markdown syntax."""
    in_fence = False
    fence_marker = ""
    for line_number, raw in enumerate(markdown.splitlines(), 1):
        fence = FENCE_RE.match(raw)
        if fence:
            marker = fence.group(1)
            if not in_fence:
                in_fence, fence_marker = True, marker
            elif marker == fence_marker:
                in_fence, fence_marker = False, ""
            continue
        if in_fence:
            continue
        text = IMAGE_RE.sub(" ", raw)
        text = LINK_RE.sub(r"\1", text)
        text = URL_RE.sub(" ", text)
        text = INLINE_CODE_RE.sub(" ", text)
        text = HTML_RE.sub(" ", text)
        text = MARKUP_RE.sub("", text).strip()
        if text and text != "---":
            yield line_number, text


def is_ascii_acronym(term: str) -> bool:
    letters = "".join(char for char in term if char.isalpha())
    return len(letters) >= 2 and letters[0].isupper() and sum(char.isupper() for char in letters) >= 2


def valid_japanese_term(term: str, pos: tuple[str, ...]) -> bool:
    if len(term) < 2 or term in STOPWORDS or HIRAGANA_RE.fullmatch(term):
        return False
    if NUMBER_RE.fullmatch(term):
        return False
    if not pos or pos[0] != "名詞":
        return False
    if len(pos) > 1 and pos[1] == "数詞":
        return False
    # Personal/place names are normally article subjects, not glossary terms.
    if len(pos) > 2 and pos[1] == "固有名詞" and pos[2] in {"人名", "地名"}:
        return False
    return True


def extract_occurrences(markdown: str) -> list[Occurrence]:
    sudachi = dictionary.Dictionary().create()
    split_mode = tokenizer.Tokenizer.SplitMode.C
    occurrences: list[Occurrence] = []

    for line_number, text in visible_lines(markdown):
        morphemes = list(sudachi.tokenize(text, split_mode))
        ascii_spans: list[tuple[int, int]] = []
        for match in ASCII_TERM_RE.finditer(text):
            term = match.group(0)
            ascii_spans.append(match.span())
            occurrences.append(
                Occurrence(term, term.casefold(), line_number, text, "ascii")
            )

        for morpheme in morphemes:
            begin, end = morpheme.begin(), morpheme.end()
            if any(begin < span_end and end > span_begin for span_begin, span_end in ascii_spans):
                continue
            term = morpheme.surface()
            pos = morpheme.part_of_speech()
            if not valid_japanese_term(term, pos):
                continue
            normalized = morpheme.normalized_form() or morpheme.dictionary_form() or term
            occurrences.append(
                Occurrence(
                    term,
                    normalized,
                    line_number,
                    text,
                    "japanese",
                    morpheme.is_oov(),
                )
            )

        # Sudachi intentionally leaves many domain terms as adjacent nouns even
        # in mode C (for example 環境+変数 and AI+エージェント). Preserve those
        # possible glossary units in addition to their individual components.
        for width in (2, 3):
            for start in range(len(morphemes) - width + 1):
                group = morphemes[start : start + width]
                if not all(is_noun(morpheme) for morpheme in group):
                    continue
                if any(morpheme.part_of_speech()[1] == "数詞" for morpheme in group):
                    continue
                if any(left.end() != right.begin() for left, right in zip(group, group[1:])):
                    continue
                term = "".join(morpheme.surface() for morpheme in group)
                if len(term) < 3 or NUMBER_RE.fullmatch(term):
                    continue
                normalized = "".join(
                    morpheme.normalized_form() or morpheme.dictionary_form() or morpheme.surface()
                    for morpheme in group
                )
                kind = "compound_ascii" if ASCII_TERM_RE.search(term) else "compound"
                occurrences.append(
                    Occurrence(
                        term,
                        normalized.casefold() if kind == "compound_ascii" else normalized,
                        line_number,
                        text,
                        kind,
                        any(morpheme.is_oov() for morpheme in group),
                    )
                )
    return occurrences


@lru_cache(maxsize=1)
def general_frequency_dictionary() -> dict[str, float]:
    """Load wordfreq's Japanese table without invoking its MeCab tokenizer."""
    return get_frequency_dict("ja")


def direct_zipf_frequency(term: str) -> float:
    """Return the precomputed Zipf frequency for one already-tokenized term."""
    probability = general_frequency_dictionary().get(term.casefold(), 0.0)
    if probability <= 0:
        return 0.0
    return max(0.0, math.log10(probability) + 9.0)


@lru_cache(maxsize=1)
def short_unit_tokenizer():
    return dictionary.Dictionary().create()


def general_zipf_frequency(term: str, kind: str) -> float:
    """Look up a term, falling back to its least-common Japanese short unit."""
    exact = direct_zipf_frequency(term)
    if exact > 0 or kind == "ascii":
        return exact
    units = [
        morpheme.normalized_form() or morpheme.dictionary_form() or morpheme.surface()
        for morpheme in short_unit_tokenizer().tokenize(term, tokenizer.Tokenizer.SplitMode.A)
        if morpheme.surface().strip()
    ]
    frequencies = [direct_zipf_frequency(unit) for unit in units]
    known = [frequency for frequency in frequencies if frequency > 0]
    if not known:
        return 0.0
    # The least familiar component limits how readily a general reader can infer
    # the compound. Unknown one-character suffixes do not zero the whole term.
    return min(known)


def candidate_score(term: str, frequency: int, unknown: bool, kind: str) -> tuple[float, float]:
    zipf = general_zipf_frequency(term, kind)
    rarity = MAX_ZIPF - zipf
    score = rarity + 0.55 * math.log2(frequency + 1)
    if "ascii" in kind:
        score += 0.5
    if kind.startswith("compound"):
        score += 0.5
    if is_ascii_acronym(term):
        score += 1.5
    if unknown:
        score += 0.75
    return round(score, 3), round(zipf, 3)


def build_candidates(markdown: str, limit: int, threshold: float) -> list[dict[str, object]]:
    occurrences = extract_occurrences(markdown)
    grouped: dict[str, list[Occurrence]] = defaultdict(list)
    for occurrence in occurrences:
        grouped[occurrence.normalized].append(occurrence)

    candidates: list[dict[str, object]] = []
    for normalized, items in grouped.items():
        surfaces = Counter(item.term for item in items)
        term = sorted(surfaces, key=lambda value: (-surfaces[value], items[0].line, value))[0]
        first = min(items, key=lambda item: item.line)
        kinds = {item.kind for item in items}
        if "compound_ascii" in kinds:
            kind = "compound_ascii"
        elif "compound" in kinds:
            kind = "compound"
        elif "ascii" in kinds:
            kind = "ascii"
        else:
            kind = "japanese"
        unknown = any(item.is_unknown for item in items)
        score, zipf = candidate_score(term, len(items), unknown, kind)
        if score < threshold:
            continue

        signals = ["low_general_frequency"]
        if "ascii" in kind:
            signals.append("latin_term")
        if kind.startswith("compound"):
            signals.append("compound_noun")
        if is_ascii_acronym(term):
            signals.append("acronym")
        if unknown:
            signals.append("sudachi_oov")
        if len(items) > 1:
            signals.append("repeated_in_article")

        candidates.append(
            {
                "term": term,
                "normalized": normalized,
                "judgment": "review",
                "score": score,
                "generalZipfFrequency": zipf,
                "articleFrequency": len(items),
                "signals": signals,
                "firstOccurrence": {
                    "line": first.line,
                    "text": first.context,
                },
            }
        )

    candidates.sort(key=lambda item: (-float(item["score"]), int(item["firstOccurrence"]["line"]), str(item["term"])))
    return candidates[:limit]


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Markdownから用語集の登録候補を抽出します。")
    parser.add_argument("article", type=Path, help="入力するarticle.md")
    parser.add_argument("-o", "--output", type=Path, help="出力先（既定: article.mdと同じ場所のglossary.json）")
    parser.add_argument("--limit", type=int, default=DEFAULT_LIMIT, help=f"最大候補数（既定: {DEFAULT_LIMIT}）")
    parser.add_argument("--threshold", type=float, default=DEFAULT_THRESHOLD, help=f"最低スコア（既定: {DEFAULT_THRESHOLD}）")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if args.limit < 1:
        raise SystemExit("--limit は1以上で指定してください")
    article = args.article.resolve()
    output = (args.output or article.with_name("glossary.json")).resolve()
    markdown = article.read_text(encoding="utf-8")
    candidates = build_candidates(markdown, args.limit, args.threshold)
    document = {
        "schemaVersion": SCHEMA_VERSION,
        "source": article.name,
        "audience": "専門知識を前提としない高校生以上の読者",
        "method": {
            "tokenizer": "SudachiPy SplitMode.C",
            "generalFrequency": "direct lookup in wordfreq Japanese frequency dictionary",
            "threshold": args.threshold,
            "limit": args.limit,
            "note": "候補抽出のみ。採否と説明文はレビューで確定する。",
        },
        "terms": candidates,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(document, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"{output}: {len(candidates)} candidates")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
