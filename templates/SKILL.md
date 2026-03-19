---
name: skill-name
description: >
  What this skill does and when to use it. Be specific — Claude uses this to
  decide when to auto-invoke. Include keywords users would naturally say.
# disable-model-invocation: true   # Uncomment for skills with side effects
# user-invocable: false            # Uncomment for background-only knowledge
# allowed-tools: Read, Grep, Glob  # Comma-separated tools granted without prompts
# context: fork                    # Uncomment to run in isolated subagent
# agent: Explore                   # Subagent type (requires context: fork)
# model: claude-sonnet-4-6         # Pin to a specific model
# argument-hint: "[arg-name]"      # Autocomplete hint for users
---

<!--
  SKILL TEMPLATE

  Replace this content with your skill's instructions.
  Keep under 500 lines — use supporting files for detailed reference material.

  Supporting files you can add alongside this SKILL.md:
  - reference.md    — Detailed docs, API references, etc.
  - examples.md     — Example inputs and expected outputs
  - scripts/        — Helper scripts the skill can execute
-->

## Purpose

Describe what this skill does in 1-2 sentences.

## Instructions

Your core instructions go here. This is what Claude follows when the skill is invoked.

## Inputs

If using arguments, describe them:
- `$ARGUMENTS` — What the user should provide
- `$0` — First positional argument

## Output

Describe what the skill should produce.
