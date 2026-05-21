#!/bin/bash
# Stop hook: runs when Claude finishes a turn
#
# Architecture lesson:
# The Stop hook fires when Claude completes its response. This is useful for:
# 1. Post-processing (format output, update status)
# 2. Quality checks (did the response meet standards?)
# 3. Notification (alert user when long task completes)
# 4. State persistence (save progress for recovery)
#
# This example notifies via terminal bell when a long operation finishes.

INPUT=$(cat)

# Send terminal bell to notify user
printf '\a'

exit 0
