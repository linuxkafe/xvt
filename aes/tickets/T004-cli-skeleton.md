---
ticket: T004
title: CLI skeleton with dry-run / confirm flags
sprint: sprint-01
priority: high
status: done
created: 2026-09-19
---

# T004 — CLI skeleton with dry-run / confirm flags

## Context
Complete the CLI with proper safety flags across all mutating commands. The scan command is read-only, but inject, patch, and flash commands need explicit confirmation and dry-run modes.

## Acceptance Criteria
- [ ] All mutating commands have `--dry-run` (default) and `--no-dry-run` / `--confirm`
- [ ] `--confirm` flag requires explicit user acknowledgment
- [ ] Dry-run shows what would be done without executing
- [ ] Structured logging with timestamps and operation details
- [ ] JSON output option for all commands
- [ ] Help text documents safety model

## Scope
**In scope:**
- Update `inject` command with proper dry-run/confirm
- Update `patch` command with proper dry-run/confirm
- Add `flash` command for firmware flashing
- Global `--verbose` / `--quiet` flags
- Structured logging (JSON lines to stderr)

**Out of scope:**
- Exploit implementation (T006+)
- Firmware modification logic (T011+)
- Actual flashing (T015+)

## Dependencies
- T002 (done): Network scanner
- T003 (done): Fingerprint database

## Rollback
Revert CLI changes in `src/main.py`

## Known Risks
- Click's confirmation prompts may not work in all CI environments
- Need to balance safety with usability for automation

## Notes
- Safety model: dry-run by default, explicit --confirm to execute
- Log format: JSON lines with timestamp, level, operation, params, result
- Consider using Python's logging module with custom formatter