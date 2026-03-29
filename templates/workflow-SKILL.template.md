---
name: workflow-name
description: >
  What this workflow does and when to use it. Workflows orchestrate multiple
  steps to accomplish end-to-end development tasks.
disable-model-invocation: true
allowed-tools: Read, Grep, Glob, Bash, Write, Edit
# context: fork                    # Uncomment for isolated execution
# model: claude-opus-4-6           # Pin to a specific model
# argument-hint: "[target]"        # Autocomplete hint
---

<!--
  WORKFLOW TEMPLATE

  Workflows are skills that orchestrate multi-step processes.
  They typically coordinate multiple actions in sequence.

  Use `disable-model-invocation: true` since workflows usually have
  side effects and should be explicitly invoked by the user.
-->

## Overview

Describe the end-to-end process this workflow automates.

## Steps

### Step 1: [Name]

What to do in this step.

### Step 2: [Name]

What to do in this step.

### Step 3: [Name]

What to do in this step.

## Completion

How to verify the workflow completed successfully.
