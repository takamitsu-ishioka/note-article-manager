---
title: "reasoning-audit readme.md"
guid: "n8b9206b3f0cf"
url: "https://note.com/kisaburo_y/n/n8b9206b3f0cf"
published: "2026-05-23 22:28:44"
modified: "2026-05-23 22:28:44"
---

# reasoning-audit readme.md

## reasoning-audit

AI-assisted logical reasoning evaluation engine.

reasoning-audit is an experimental platform for evaluating logical reasoning processes rather than memorized knowledge.

The system is designed around a simple idea:

> In the age of generative AI, the important skill is no longer "answering without tools", but "reasoning correctly with tools".

---

## Core Concepts

Traditional examinations primarily evaluate:

- memorization
- speed
- isolated problem solving

This project explores a different direction.

reasoning-audit evaluates:

- logical consistency
- assumption clarity
- counterexample analysis
- reasoning trace quality
- ability to verify AI-generated outputs

The focus is not only the final answer, but also the reasoning process that led to it.

---

## Features

- AI-assisted problem generation
- Reasoning-process evaluation
- LLM-based scoring
- Structured reasoning traces
- PostgreSQL backend
- Self-hosted deployment
- VM-friendly architecture
- API-first design
- Source code included

---

## Non-Goals

This project intentionally does NOT aim to provide:

- anti-cheat systems
- AI usage restrictions
- closed question banks
- memorization-oriented exams
- high-availability infrastructure
- enterprise workflow integrations

The philosophy is:

> AI usage is allowed. The ability being evaluated is how reasoning is constructed, verified, and corrected.

---

## Example Workflow

1. Generate a logic problem
2. Submit:
  - final answer
  - reasoning trace
3. Evaluate using LLMs
4. Store structured evaluation results
5. Return feedback

Example evaluation dimensions:

- logical_consistency
- assumption_clarity
- contradiction_detection
- counterexample_analysis

---

## Example Evaluation Output

```
{
  "logical_consistency": 0.91,
  "assumption_clarity": 0.74,
  "counterexample_analysis": 0.88,
  "feedback": [
    "Counterexample handling is strong",
    "Some assumptions are implicit"
  ]
}
```

---

## Architecture

Current design goals:

- single VM deployment
- PostgreSQL backend
- REST API
- JSON-based interfaces
- pluggable LLM providers

Supported / planned providers:

- OpenAI
- Anthropic
- Gemini
- local LLMs

---

## Why Open Source?

Reasoning evaluation systems should be inspectable.

This repository intentionally exposes:

- evaluation logic
- prompts
- scoring structures
- reasoning schemas

The project values transparency over black-box scoring.

---

## Intended Use Cases

- education
- AI-assisted learning
- reasoning research
- engineering interviews
- internal training
- experimental cognitive tooling

---

## Current Status

Early experimental phase.

The project currently prioritizes:

- core reasoning models
- evaluation stability
- reasoning trace structures

over UI polish or production scalability.

---

## License

TBD

Commercial support, consulting, and custom deployments may be offered separately.

---

## Author

Kisaburo Yamada

Experimental project exploring reasoning evaluation in the generative AI era.
