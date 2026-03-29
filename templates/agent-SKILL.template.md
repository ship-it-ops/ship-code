---
name: agent-name
description: >
  What this agent does and when to use it. Agents are skills that run in
  isolated subagent contexts for complex, multi-step tasks.
context: fork
agent: Explore
allowed-tools: Read, Grep, Glob, Bash
# disable-model-invocation: true   # Uncomment for agents with side effects
# model: claude-opus-4-6           # Pin to a specific model
# argument-hint: "[target]"        # Autocomplete hint
---

<!--
  AGENT TEMPLATE

  Agents are skills that use `context: fork` to run in an isolated subagent.
  The agent type (Explore, Plan, general-purpose) determines capabilities.

  Agent types:
  - Explore: Fast codebase exploration (read-only)
  - Plan: Architecture and design planning (read-only)
  - general-purpose: Full capabilities including edits
-->

## Role

Describe this agent's role and responsibilities.

## Process

1. First, do this...
2. Then, do this...
3. Finally, produce this output...

## Output Format

Describe the expected output structure.
