"""
Masarie Patterns FAQ Diagnostic
===============================

V1: Single-file FAQ/customer-question intelligence prototype.

Purpose
-------
Analyze a customer-facing FAQ as if we were trying to answer:

    "Will this FAQ actually prevent customers from calling?"

This is NOT an AI chatbot.

Instead, V1 provides a mechanical diagnostic of the FAQ:

    * Parse FAQ sections and questions
    * Measure answer lengths
    * Identify unusually short/long answers
    * Detect potentially technical terminology
    * Identify question types
    * Identify repeated concepts
    * Identify weakly covered customer-journey stages
    * Generate likely "next questions"
    * Produce a human-readable report
    * Export structured JSON for future V2 work

Input
-----
A plain-text FAQ file.

Example:

    python masarie_faq_diagnostic.py masarie_patterns_faq.txt

Optional:

    python masarie_faq_diagnostic.py masarie_patterns_faq.txt \
        --json faq_analysis.json

Design philosophy
-----------------
Keep V1 boring.

No API.
No database.
No web server.
No framework.

The goal is to establish a clean data model and customer-question
analysis pipeline that V2 can build upon.

Author: Alex Masarie
Project: weDHack26 / Masarie Patterns
"""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Optional


# ============================================================
# CONFIGURATION
# ============================================================

LONG_ANSWER_WORDS = 150
SHORT_ANSWER_WORDS = 20

# Terms that a person starting a fashion brand might not know.
JARGON_TERMS = {
    "CAD",
    "DXF",
    "PDS",
    "HPG",
    "HPGL",
    "PLT",
    "CLO 3D",
    "Optitex",
    "Lectra",
    "Gerber",
    "tech pack",
    "oak tag",
    "patternmaking",
    "pattern grading",
    "grading",
    "fit model",
    "mock-up",
    "sew-by",
    "production-ready",
    "avatar",
    "intellectual property",
    "IP",
    "drafting",
    "manufacturer",
    "production run",
    "base size",
}

# Words that help us classify what a customer is asking about.
QUESTION_TYPES = {
    "cost": {
        "cost",
        "price",
        "pricing",
        "fee",
        "fees",
        "payment",
        "deposit",
        "expensive",
        "charge",
        "quote",
    },
    "timeline": {
        "how long",
        "timeline",
        "when",
        "how soon",
        "months",
        "days",
        "weeks",
    },
    "process": {
        "how",
        "process",
        "steps",
        "start",
        "begin",
        "happen",
        "sample",
        "revision",
        "fitting",
    },
    "ownership": {
        "own",
        "ownership",
        "rights",
        "reuse",
        "intellectual",
        "IP",
        "pattern",
        "copyright",
    },
    "production": {
        "production",
        "manufacturing",
        "manufacturer",
        "factory",
        "inventory",
        "produce",
        "production-ready",
    },
    "materials": {
        "material",
        "fabric",
        "swatch",
        "sourcing",
        "textile",
    },
    "technical": {
        "software",
        "file",
        "format",
        "CAD",
        "DXF",
        "tech pack",
        "pattern",
    },
    "fitting": {
        "fit",
        "fitting",
        "model",
        "sample",
        "mobility",
        "comfort",
        "proportion",
    },
    "communication": {
        "contact",
        "virtual",
        "in person",
        "local",
        "virtually",
        "communication",
    },
}


# ============================================================
# DATA STRUCTURES
# ============================================================

@dataclass
class FAQItem:
    """One parsed FAQ question and answer."""

    section: str
    question: str
    answer: str
    word_count: int = 0
    question_type: str = "general"
    jargon: list[str] | None = None
    follow_up_questions: list[str] | None = None

    def __post_init__(self):
        self.word_count = count_words(self.answer)
        self.jargon = self.jargon or []
        self.follow_up_questions = self.follow_up_questions or []


# ============================================================
# BASIC TEXT FUNCTIONS
# ============================================================

def count_words(text: str) -> int:
    """Return approximate word count."""

    return len(
        re.findall(
            r"\b[\w'-]+\b",
            text,
            flags=re.UNICODE,
        )
    )


def normalize(text: str) -> str:
    """Normalize whitespace for comparison/search."""

    return re.sub(r"\s+", " ", text).strip()


def clean_question(question: str) -> str:
    """Normalize a question while preserving readable text."""

    question = normalize(question)

    return question


# ============================================================
# SECTION DETECTION
# ============================================================

def looks_like_section(line: str) -> bool:
    """
    Heuristic section detector.

    Annie's FAQ uses emoji headings such as:

        🧭 Getting Started
        🧵 Understanding the Process

    We therefore treat short lines beginning with a non-word
    character as possible headings, provided they aren't questions.
    """

    if not line:
        return False

    if line.endswith("?"):
        return False

    if len(line) > 100:
        return False

    first_char = line[0]

    # Emoji / symbol heuristic.
    if not first_char.isalnum():
        return True

    # Also recognize common all-caps headings.
    if line.upper() == line and len(line.split()) <= 8:
        return True

    return False


# ============================================================
# FAQ PARSER
# ============================================================

def parse_faq(text: str) -> list[FAQItem]:
    """
    Parse a plain-text FAQ into FAQItem objects.

    Expected structure:

        SECTION

        Question?
        Answer.

        Another question?
        Another answer.
    """

    lines = [
        normalize(line)
        for line in text.splitlines()
    ]

    current_section = "Uncategorized"
    current_question: Optional[str] = None
    current_answer: list[str] = []

    faq: list[FAQItem] = []

    def save_current():
        nonlocal current_question
        nonlocal current_answer

        if current_question:
            answer = normalize(" ".join(current_answer))

            faq.append(
                FAQItem(
                    section=current_section,
                    question=clean_question(current_question),
                    answer=answer,
                )
            )

        current_question = None
        current_answer = []

    for line in lines:

        if not line:
            continue

        # Section heading
        if looks_like_section(line):
            save_current()
            current_section = line
            continue

        # Question
        if line.endswith("?"):
            save_current()
            current_question = line
            continue

        # Answer content
        if current_question:
            current_answer.append(line)

    save_current()

    return faq


# ============================================================
# JARGON ANALYSIS
# ============================================================

def find_jargon(text: str) -> list[str]:
    """Find potentially technical terms."""

    found = []

    for term in JARGON_TERMS:

        pattern = rf"(?<!\w){re.escape(term)}(?!\w)"

        if re.search(
            pattern,
            text,
            flags=re.IGNORECASE,
        ):
            found.append(term)

    return sorted(found, key=str.lower)


def jargon_frequency(faq: list[FAQItem]) -> Counter:
    """Count jargon appearances across FAQ items."""

    counter = Counter()

    for item in faq:
        for term in find_jargon(
            item.question + " " + item.answer
        ):
            counter[term] += 1

    return counter


# ============================================================
# QUESTION CLASSIFICATION
# ============================================================

def classify_question(question: str) -> str:
    """
    Assign a rough intent category.

    This is deliberately simple and transparent.
    V2 can replace this with semantic classification.
    """

    q = question.lower()

    scores = {}

    for category, keywords in QUESTION_TYPES.items():

        score = 0

        for keyword in keywords:
            if keyword.lower() in q:
                score += 1

        scores[category] = score

    best_category = max(
        scores,
        key=scores.get,
    )

    if scores[best_category] == 0:
        return "general"

    return best_category


# ============================================================
# CUSTOMER JOURNEY
# ============================================================

CUSTOMER_JOURNEY = [
    "Idea / Concept",
    "Getting Started",
    "Design Development",
    "Pattern / Tech Pack",
    "Sample / Prototype",
    "Fitting / Revision",
    "Production",
    "Manufacturing",
    "Delivery / Handoff",
    "Ownership / Rights",
]


def section_journey_signal(section: str) -> str:
    """Map FAQ sections to broad customer journey stages."""

    s = section.lower()

    if "getting started" in s:
        return "Getting Started"

    if "process" in s:
        return "Design Development"

    if "timeline" in s:
        return "Sample / Prototype"

    if "pricing" in s:
        return "Getting Started"

    if "production" in s:
        return "Production"

    if "ownership" in s or "rights" in s:
        return "Ownership / Rights"

    return "General"


# ============================================================
# FOLLOW-UP QUESTION GENERATION
# ============================================================

def generate_followups(item: FAQItem) -> list[str]:
    """
    Generate obvious follow-up questions based on the question.

    These aren't AI-generated.

    They are deliberately conservative prompts for human review.
    """

    q = item.question.lower()

    followups = []

    if any(word in q for word in ["cost", "price", "pricing"]):
        followups.extend([
            "What exactly is included in that price?",
            "What could cause the price to increase?",
            "What happens if my project changes?",
        ])

    if "how long" in q or "timeline" in q:
        followups.extend([
            "What could make the timeline longer?",
            "When do I receive my first sample?",
            "What part of the process usually takes the longest?",
        ])

    if "tech pack" in q:
        followups.extend([
            "Do I actually need a tech pack?",
            "What does a tech pack include?",
            "Can I create or edit the tech pack myself?",
        ])

    if "pattern" in q:
        followups.extend([
            "What exactly do I receive with my pattern?",
            "Can another manufacturer use my pattern?",
            "What happens if the pattern needs changes?",
        ])

    if "manufacturer" in q or "production" in q:
        followups.extend([
            "Do you help me find a manufacturer?",
            "Who handles communication with the factory?",
            "Can you help with a small production run?",
        ])

    if "fit" in q or "fitting" in q:
        followups.extend([
            "What happens if the garment doesn't fit?",
            "How many fitting rounds are included?",
            "Do I need to be there in person?",
        ])

    if "own" in q or "rights" in q:
        followups.extend([
            "Can I use my pattern with another manufacturer?",
            "Can another customer receive the same pattern?",
            "Can I modify the pattern later?",
        ])

    # Remove duplicates while preserving order.
    return list(dict.fromkeys(followups))


# ============================================================
# COVERAGE / GAP ANALYSIS
# ============================================================

def analyze_section_coverage(
    faq: list[FAQItem],
) -> dict[str, int]:

    coverage = Counter()

    for item in faq:

        journey_stage = section_journey_signal(
            item.section
        )

        coverage[journey_stage] += 1

    return dict(coverage)


def identify_potential_gaps(
    faq: list[FAQItem],
) -> list[str]:

    coverage = analyze_section_coverage(faq)

    gaps = []

    for stage in CUSTOMER_JOURNEY:

        count = coverage.get(stage, 0)

        if count == 0:
            gaps.append(
                f"No obvious FAQ coverage for: {stage}"
            )

        elif count == 1:
            gaps.append(
                f"Very light FAQ coverage for: {stage}"
            )

    return gaps


# ============================================================
# REPEATED CONCEPT ANALYSIS
# ============================================================

CONCEPTS = {
    "pattern": ["pattern", "patterns"],
    "tech pack": ["tech pack", "techpack"],
    "sample": ["sample", "sampling"],
    "production": ["production", "manufacturing", "manufacturer"],
    "fit": ["fit", "fitting"],
    "pricing": ["price", "pricing", "cost", "fee", "payment"],
    "ownership": ["ownership", "rights", "IP", "intellectual property"],
    "materials": ["materials", "fabric", "swatches"],
    "revision": ["revision", "revisions", "updates"],
}


def concept_frequency(
    faq: list[FAQItem],
) -> Counter:

    counter = Counter()

    for item in faq:

        text = (
            item.question + " " + item.answer
        ).lower()

        for concept, terms in CONCEPTS.items():

            if any(term.lower() in text for term in terms):
                counter[concept] += 1

    return counter


# ============================================================
# REPORT DATA
# ============================================================

def analyze_faq(
    faq: list[FAQItem],
) -> dict:

    # Enrich individual items.
    for item in faq:

        item.question_type = classify_question(
            item.question
        )

        item.jargon = find_jargon(
            item.question + " " + item.answer
        )

        item.follow_up_questions = generate_followups(
            item
        )

    answer_lengths = [
        item.word_count
        for item in faq
    ]

    total_words = sum(answer_lengths)

    average_words = (
        total_words / len(answer_lengths)
        if answer_lengths
        else 0
    )

    section_counts = Counter(
        item.section
        for item in faq
    )

    question_types = Counter(
        item.question_type
        for item in faq
    )

    return {
        "total_questions": len(faq),
        "total_answer_words": total_words,
        "average_answer_words": round(
            average_words,
            1,
        ),
        "section_counts": dict(section_counts),
        "question_types": dict(question_types),
        "jargon_frequency": dict(
            jargon_frequency(faq)
        ),
        "concept_frequency": dict(
            concept_frequency(faq)
        ),
        "coverage": analyze_section_coverage(faq),
        "potential_gaps": identify_potential_gaps(
            faq
        ),
        "long_answers": [
            item.question
            for item in faq
            if item.word_count >= LONG_ANSWER_WORDS
        ],
        "short_answers": [
            item.question
            for item in faq
            if item.word_count <= SHORT_ANSWER_WORDS
        ],
        "faq_items": [
            asdict(item)
            for item in faq
        ],
    }


# ============================================================
# HUMAN-READABLE REPORT
# ============================================================

def print_report(
    faq: list[FAQItem],
    analysis: dict,
):

    print()
    print("=" * 78)
    print("MASARIE PATTERNS — FAQ BETA-TEST DIAGNOSTIC")
    print("=" * 78)

    # --------------------------------------------------------

    print("\nOVERVIEW")
    print("-" * 78)

    print(
        f"Questions:              "
        f"{analysis['total_questions']}"
    )

    print(
        f"Answer words:           "
        f"{analysis['total_answer_words']}"
    )

    print(
        f"Average answer:         "
        f"{analysis['average_answer_words']} words"
    )

    # --------------------------------------------------------

    print("\nQUESTIONS BY SECTION")
    print("-" * 78)

    for section, count in analysis[
        "section_counts"
    ].items():

        print(
            f"{count:>3}  {section}"
        )

    # --------------------------------------------------------

    print("\nQUESTION TYPES")
    print("-" * 78)

    for question_type, count in sorted(
        analysis["question_types"].items(),
        key=lambda x: (-x[1], x[0]),
    ):

        print(
            f"{count:>3}  {question_type}"
        )

    # --------------------------------------------------------

    print("\nCUSTOMER-JOURNEY COVERAGE")
    print("-" * 78)

    for stage in CUSTOMER_JOURNEY:

        count = analysis[
            "coverage"
        ].get(stage, 0)

        marker = (
            "✓"
            if count >= 2
            else "?"
            if count == 1
            else "!"
        )

        print(
            f"{marker} {count:>2}  {stage}"
        )

    # --------------------------------------------------------

    print("\nPOTENTIAL GAPS")
    print("-" * 78)

    for gap in analysis[
        "potential_gaps"
    ]:

        print(
            f"  ⚠ {gap}"
        )

    # --------------------------------------------------------

    print("\nPOTENTIAL JARGON")
    print("-" * 78)

    jargon = analysis[
        "jargon_frequency"
    ]

    if jargon:

        for term, count in sorted(
            jargon.items(),
            key=lambda x: (-x[1], x[0].lower()),
        ):

            print(
                f"  {count:>2}x  {term}"
            )

    else:
        print("  None detected.")

    # --------------------------------------------------------

    print("\nREPEATED CONCEPTS")
    print("-" * 78)

    for concept, count in sorted(
        analysis["concept_frequency"].items(),
        key=lambda x: (-x[1], x[0]),
    ):

        print(
            f"  {count:>2} questions mention "
            f"{concept}"
        )

    # --------------------------------------------------------

    print("\nLONG ANSWERS — REVIEW MANUALLY")
    print("-" * 78)

    if analysis["long_answers"]:

        for question in analysis[
            "long_answers"
        ]:

            print(
                f"  ⚠ {question}"
            )

    else:
        print("  None.")

    # --------------------------------------------------------

    print("\nVERY SHORT ANSWERS — REVIEW MANUALLY")
    print("-" * 78)

    if analysis["short_answers"]:

        for question in analysis[
            "short_answers"
        ]:

            print(
                f"  ? {question}"
            )

    else:
        print("  None.")

    # --------------------------------------------------------

    print("\nLIKELY CUSTOMER FOLLOW-UP QUESTIONS")
    print("-" * 78)

    for item in faq:

        if not item.follow_up_questions:
            continue

        print(f"\n{item.question}")

        for followup in item.follow_up_questions:

            print(
                f"    → {followup}"
            )

    # --------------------------------------------------------

    print("\nCUSTOMER-TEST PROMPTS")
    print("-" * 78)

    print(
        """
Pretend you know absolutely nothing about fashion development.

Ask:

  • I only have an idea. Can you help me?
  • What exactly am I paying you to do?
  • What do I get when you're finished?
  • What happens if I don't like the sample?
  • What happens if I change my design?
  • Who finds my manufacturer?
  • What happens after you finish my pattern?
  • What does "one style" mean?
  • How involved do I need to be?
  • What could cause the project to cost more?
  • What happens if I am not local?
  • What happens after production begins?

These are intentionally human-review prompts.
V2 should automate this process.
"""
    )

    print("=" * 78)
    print()


# ============================================================
# JSON EXPORT
# ============================================================

def save_json(
    analysis: dict,
    output_path: Path,
):

    output_path.write_text(
        json.dumps(
            analysis,
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    print(
        f"\nJSON analysis written to:"
        f"\n  {output_path}"
    )


# ============================================================
# COMMAND LINE
# ============================================================

def parse_args():

    parser = argparse.ArgumentParser(
        description=(
            "Analyze a customer-facing FAQ "
            "for clarity, coverage, jargon, "
            "and likely customer follow-up questions."
        )
    )

    parser.add_argument(
        "faq_file",
        type=Path,
        help="Plain-text FAQ file",
    )

    parser.add_argument(
        "--json",
        type=Path,
        default=None,
        help="Optional JSON output file",
    )

    return parser.parse_args()


# ============================================================
# MAIN
# ============================================================

def main():

    args = parse_args()

    if not args.faq_file.exists():

        raise SystemExit(
            f"ERROR: File not found: "
            f"{args.faq_file}"
        )

    text = args.faq_file.read_text(
        encoding="utf-8"
    )

    faq = parse_faq(text)

    if not faq:

        raise SystemExit(
            "ERROR: No FAQ questions detected."
        )

    analysis = analyze_faq(faq)

    print_report(
        faq,
        analysis,
    )

    if args.json:

        save_json(
            analysis,
            args.json,
        )


if __name__ == "__main__":
    main()
