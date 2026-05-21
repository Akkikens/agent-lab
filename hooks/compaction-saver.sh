#!/bin/bash
# PreCompact hook: saves context state before automatic compaction
#
# Architecture lesson:
# When Claude Code's context window fills up, it COMPACTS — summarizing older
# messages to free space. This is lossy. Critical state can be lost.
#
# This hook fires BEFORE compaction happens, giving you a chance to:
# 1. Save important state to a file (persists beyond compaction)
# 2. Log what's being compacted (debugging context issues)
# 3. Alert the user that compaction is happening
#
# Context compaction is the #1 source of "Claude forgot what we were doing"
# — this hook mitigates that by persisting state externally.

INPUT=$(cat)
TIMESTAMP=$(date -Iseconds)
SAVE_DIR="/Users/akshay/Documents/GitHub/agent-lab/.claude/compaction-snapshots"
mkdir -p "$SAVE_DIR"

# Save the compaction event with any available context
echo "{\"ts\":\"$TIMESTAMP\",\"event\":\"pre_compaction\"}" >> "$SAVE_DIR/compaction-log.jsonl"

# The hook could also write a summary file that gets re-read post-compaction
# to restore critical state. For now, just log.

exit 0
