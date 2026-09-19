---
ticket: T005
title: Logging + structured output (JSON)
sprint: sprint-01
priority: high
status: done
created: 2026-09-19
---

# T005 — Logging + structured output (JSON)

## Context
Implement structured logging with JSON lines output for all operations. This enables automation, debugging, and audit trails.

## Acceptance Criteria
- [ ] JSON lines logging to stderr with timestamp, level, operation, params, result
- [ ] `--json-logs` flag enables JSON output
- [ ] `--verbose`/`-v` and `--quiet`/`-q` flags control log level
- [ ] All CLI commands log their operations
- [ ] Dry-run and confirm actions are logged
- [ ] Log format is machine-parseable

## Scope
**In scope:**
- JSONFormatter class for structured logging
- setup_logging() function with verbose/quiet/json-logs options
- log_operation() helper for consistent operation logging
- Integration in all CLI commands (scan, inject, patch, flash, vectors)

**Out of scope:**
- Log rotation/persistence (file output)
- Centralized log aggregation

## Dependencies
- T004 (done): CLI skeleton

## Rollback
Remove JSONFormatter, setup_logging, log_operation from main.py

## Known Risks
- JSON logs to stderr may interfere with command JSON output (stdout)
- Large param objects may make logs verbose

## Notes
- Implemented in src/main.py alongside CLI
- Uses Python's logging module with custom JSONFormatter
- Extra fields passed via `extra` parameter
- Timestamp in ISO8601 UTC format