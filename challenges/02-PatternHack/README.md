The second challenge shall be:

# Masarie Patterns Customer Intelligence Prototype

**weDHack26 Prototype**

> Turn repetitive customer questions into an intelligent, continuously improving FAQ and customer-intake system.

---

## 🎯 The Problem

Masarie Patterns is receiving a high volume of customer inquiries, including many from people who are unfamiliar with the fashion-development process.

The existing FAQ addresses many common questions, but a static FAQ has an inherent limitation:

**We don't know what questions customers will ask until they ask them.**

The goal of this prototype is to create a lightweight system that:

1. Answers common customer questions using approved Masarie Patterns information.
2. Recognizes when it does not know the answer.
3. Captures unanswered or ambiguous questions.
4. Identifies recurring question patterns.
5. Suggests additions or improvements to the FAQ.
6. Eventually assists with incoming email.
7. Keeps a human in control of customer-facing communication.

---

# 🧠 Core Concept

```text
                    MASARIE PATTERNS
                           │
                           ▼
                  ┌─────────────────┐
                  │  KNOWLEDGE BASE │
                  │                 │
                  │  FAQ            │
                  │  Services       │
                  │  Policies       │
                  │  Process        │
                  └────────┬────────┘
                           │
                           ▼
                      CUSTOMER
                           │
                           ▼
                    ┌─────────────┐
                    │   QUESTION  │
                    └──────┬──────┘
                           │
                           ▼
                  ┌─────────────────┐
                  │ QUESTION MATCHER│
                  └───────┬─────────┘
                          │
                 ┌────────┴────────┐
                 │                 │
              CONFIDENT         UNCERTAIN
                 │                 │
                 ▼                 ▼
          APPROVED ANSWER     HUMAN REVIEW
                 │                 │
                 │                 ▼
                 │           QUESTION LOG
                 │                 │
                 └────────┬────────┘
                          ▼
                  FAQ GAP ANALYSIS
                          │
                          ▼
                  BETTER FAQ / BETTER
                    CUSTOMER SERVICE
```

---

# 🏗️ V2 Architecture

Start simple.

```text
masarie-patterns-ai/
│
├── README.md
│
├── data/
│   ├── faq.txt
│   ├── faq.json
│   └── questions.jsonl
│
├── src/
│   ├── parser.py
│   ├── faq_store.py
│   ├── question_classifier.py
│   ├── matcher.py
│   ├── confidence.py
│   ├── gap_analysis.py
│   └── reporting.py
│
├── scripts/
│   ├── analyze_faq.py
│   ├── ingest_questions.py
│   └── generate_report.py
│
├── tests/
│   ├── test_parser.py
│   ├── test_matcher.py
│   └── test_classifier.py
│
├── examples/
│   └── sample_questions.txt
│
└── .gitignore
```

---

# 🚀 PHASE 1 — FAQ Knowledge Base

The existing FAQ should become structured data.

Example:

```json
{
  "id": "getting-started-001",
  "category": "Getting Started",
  "question": "What do you need from me to get started?",
  "answer": "We can start anywhere...",
  "keywords": [
    "sketch",
    "reference garment",
    "images",
    "concept"
  ]
}
```

### TODO

* [ ] Convert Annie's current FAQ into structured JSON.
* [ ] Preserve the original wording.
* [ ] Assign stable IDs to every FAQ item.
* [ ] Add categories.
* [ ] Add optional keywords.
* [ ] Add source/version metadata.
* [ ] Add `last_reviewed`.
* [ ] Add `approved_by`.

---

# 🔎 PHASE 2 — Question Matching

Given:

> "I don't have a tech pack yet. Can you still help me?"

Find:

> "What if I already have a tech pack or don't need one?"

and/or:

> "What do you need from me to get started?"

The system should return:

```text
BEST MATCH
-----------
Question:
What do you need from me to get started?

Confidence:
0.87

Category:
Getting Started
```

### TODO

* [ ] Start with keyword matching.
* [ ] Add TF-IDF similarity.
* [ ] Compare keyword vs semantic approaches.
* [ ] Establish a confidence score.
* [ ] Return top 3 candidate answers.
* [ ] Never automatically answer below a confidence threshold.

---

# 🤖 PHASE 3 — AI-Assisted Answering

Once deterministic retrieval works, add an LLM.

Important:

**The LLM does not become the source of truth.**

The FAQ/knowledge base remains the source of truth.

The LLM's job is to:

1. Understand the customer's question.
2. Retrieve relevant approved information.
3. Formulate a friendly response.
4. Admit uncertainty when information is unavailable.

Conceptually:

```text
Customer question
       ↓
Retrieve relevant FAQ
       ↓
Context
       ↓
LLM
       ↓
Draft answer
       ↓
Confidence / policy check
       ↓
Human OR customer
```

### TODO

* [ ] Choose LLM provider.
* [ ] Create prompt template.
* [ ] Restrict answers to retrieved Masarie information.
* [ ] Add explicit "I don't know" behavior.
* [ ] Test hallucination resistance.
* [ ] Log every generated answer.
* [ ] Keep human approval enabled initially.

---

# 🕳️ PHASE 4 — FAQ GAP DETECTION

This is the secret sauce.

Every question that cannot be confidently answered gets logged.

Example:

```text
QUESTION
--------
"Can you help me find a manufacturer for a small first run?"

MATCH
-----
None

CATEGORY
--------
Production

STATUS
------
Unanswered
```

After 30 similar questions:

```text
FAQ GAP DETECTED

Theme:
Manufacturer selection

Questions:
31

Recommendation:
Consider adding a FAQ entry addressing:

"Can you help me find a manufacturer?"
```

### TODO

* [ ] Store unanswered questions.
* [ ] Cluster semantically similar questions.
* [ ] Count recurring themes.
* [ ] Rank by frequency.
* [ ] Rank by business importance.
* [ ] Generate proposed FAQ questions.
* [ ] Require Annie approval before publication.

---

# 📬 PHASE 5 — EMAIL ASSISTANT

Eventually connect the system to Annie's email.

Incoming:

```text
Hi!

I have a sketch for a jacket but don't know
anything about tech packs. Is this something
you can help me with?

Thanks!
```

System:

```text
CATEGORY
Getting Started

FAQ MATCH
"What do you need from me to get started?"

CONFIDENCE
0.94

DRAFT RESPONSE
----------------
Hi!

Absolutely. We can start with a rough sketch,
reference garment, or reference images...

[VIEW SOURCE FAQ]
[EDIT]
[APPROVE & SEND]
```

**Do not auto-send initially.**

### TODO

* [ ] Connect Gmail.
* [ ] Read incoming messages.
* [ ] Extract customer question.
* [ ] Retrieve relevant FAQ.
* [ ] Generate draft.
* [ ] Present draft to Annie.
* [ ] Add approve/edit/reject workflow.
* [ ] Log final response.
* [ ] Compare AI draft with final human response.

---

# 📊 PHASE 6 — Customer Intelligence Dashboard

The system should eventually answer:

### What are customers asking?

```text
Getting Started       42%
Pricing                21%
Production             15%
Tech Packs             9%
Fitting                7%
Ownership               6%
```

### What questions are increasing?

```text
Manufacturer questions       ↑ 340%
Tech pack questions           ↑ 120%
Pricing questions             → stable
Ownership questions           ↓
```

### What does the FAQ fail to answer?

```text
1. Finding a manufacturer       31 questions
2. Small production runs       19 questions
3. Cost of tech packs          14 questions
4. What happens after sample    9 questions
```

### TODO

* [ ] Add basic dashboard.
* [ ] Plot question categories.
* [ ] Plot unanswered questions.
* [ ] Plot question trends over time.
* [ ] Add top recurring questions.
* [ ] Add FAQ recommendations.

---

# 🧪 PHASE 7 — Evaluation

Do not judge the system by whether it sounds clever.

Build a test set.

Example:

```text
customer question
        ↓
expected FAQ
        ↓
actual FAQ
        ↓
correct / incorrect
```

Create at least:

* 20 obvious questions
* 20 paraphrased questions
* 20 ambiguous questions
* 20 questions outside the FAQ
* 20 adversarial / misleading questions

Target:

```text
Retrieval accuracy > 90%

False confident answers → ~0

Unknown questions correctly escalated → >95%
```

---

# 🔐 Human-in-the-Loop Rules

The prototype must follow these rules:

### Rule 1

The system may answer only from approved Masarie Patterns information.

### Rule 2

If confidence is low, say so.

### Rule 3

Legal/IP questions should be escalated rather than improvised.

### Rule 4

Pricing should never be invented.

### Rule 5

The system should distinguish:

```text
KNOWN
RELATED
UNKNOWN
HUMAN REQUIRED
```

### Rule 6

Annie remains the final authority on published FAQ content.

---

# ✨ The "Pop" Features

These are intentionally optional.

## "Why did you answer that?"

Every answer should be able to expose:

```text
ANSWER SOURCE

✓ FAQ #GS-001
✓ FAQ #GS-003

Confidence: 0.91
```

---

## "Suggest an FAQ"

After enough unanswered questions:

```text
💡 NEW FAQ SUGGESTION

Customers have asked 17 variations of:

"Can you help me find a manufacturer?"

Suggested FAQ:

Q: Can you help me find a manufacturer?

[EDIT]
[APPROVE]
[REJECT]
```

---

## "Question Heat Map"

Visualize the customer journey:

```text
IDEA
████████████

DESIGN
████████

PATTERN
██████████████

SAMPLE
████████████████

PRODUCTION
███████████████████████

OWNERSHIP
████
```

This immediately shows Annie where customers are getting stuck.

---

# 🧰 Technology Progression

Do not overbuild.

### V1

```text
Python
TXT
JSON
Regex
CLI
```

### V2

```text
Python
JSON / SQLite
scikit-learn
embeddings
semantic search
```

### V3

```text
Python
FastAPI
SQLite/PostgreSQL
LLM API
Gmail API
Web UI
```

### V4

```text
Hosted application
Authentication
Analytics
Admin dashboard
Customer-facing assistant
```

---

# 🧑‍💻 PyCharm TODO List

Create these TODO comments directly in the project.

```python
# TODO: Convert FAQ text into canonical JSON records.
# TODO: Assign stable IDs to FAQ records.
# TODO: Add FAQ versioning.
# TODO: Add source attribution.
# TODO: Build deterministic keyword matcher.
# TODO: Implement TF-IDF similarity.
# TODO: Compare keyword and semantic retrieval.
# TODO: Add confidence scoring.
# TODO: Add "unknown" threshold.
# TODO: Build question logging.
# TODO: Store unanswered questions.
# TODO: Cluster unanswered questions.
# TODO: Detect recurring question themes.
# TODO: Generate FAQ-gap recommendations.
# TODO: Build evaluation/test dataset.
# TODO: Measure retrieval accuracy.
# TODO: Add LLM only after deterministic retrieval works.
# TODO: Add retrieval-augmented generation.
# TODO: Add citation/source display to generated answers.
# TODO: Add human approval workflow.
# TODO: Connect Gmail.
# TODO: Generate email drafts.
# TODO: NEVER auto-send during prototype phase.
# TODO: Build question analytics dashboard.
# TODO: Add trend analysis.
# TODO: Add FAQ recommendation dashboard.
# TODO: Add exportable weekly report.
```

---

# 🏆 Definition of a Successful weDHack26 Demo

The demo should be possible in under five minutes.

### Step 1

Annie enters:

> "I have a sketch but no tech pack. Can you help?"

### Step 2

System finds the relevant FAQ.

### Step 3

System produces a draft answer.

### Step 4

Annie asks something the FAQ doesn't answer:

> "Can you help me find a manufacturer for a 50-piece first run?"

System responds:

```text
I don't have an approved answer for this question.

I've logged it as a potential FAQ gap.
```

### Step 5

Show dashboard:

```text
NEW FAQ GAP

"Finding a manufacturer"

17 customer questions

[GENERATE FAQ SUGGESTION]
```

### Step 6

Click:

**Generate FAQ Suggestion**

System produces a draft.

Annie edits it.

Click:

**Approve**

Done.

---

# 🎁 The Actual Product Idea

This is bigger than a chatbot.

The product is:

## A self-improving customer knowledge system for small businesses.

Most small businesses don't know what their customers are confused about.

They only know what customers ask them.

This system turns:

```text
CUSTOMER QUESTIONS
        ↓
KNOWLEDGE
        ↓
BETTER FAQ
        ↓
FEWER REPETITIVE QUESTIONS
        ↓
MORE CUSTOMER INTELLIGENCE
```

Masarie Patterns is simply the first real-world laboratory.

---

# 🚧 First weDHack26 Milestone

Do NOT build the whole thing.

Build this:

```text
FAQ
 ↓
Parser
 ↓
Structured JSON
 ↓
Question matcher
 ↓
Confidence score
 ↓
Known / Unknown
 ↓
Question log
 ↓
Gap report
```

If that works reliably, **then** add AI.

The first goal is not:

> "Build an AI chatbot."

The first goal is:

> **"Build a machine that can tell Annie what her customers are trying to figure out."**

