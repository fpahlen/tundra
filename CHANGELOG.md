# Changelog

## v1.2

- **Grok Build skill** at `.grok/skills/tundra/` (`/tundra` extract · validate · implement)
- Self-contained `references/` (format, prompts, example model) for user-wide install
- README: Use with Grok Build + optional `AGENTS.md` snippet

## v1.1.1

- Documented **scope and blindspots** (README + `docs/scope-and-blindspots.md`)
- Clarified that the five concepts target durable domain obligations, not every quality of long-running software

## v1.1

Promotable methodology pack.

### Format

- Processes gain light structure: **Actor**, **Requires**, **Results**
- Scenario vocabulary documented: `is broken` vs `is applied`
- README rewritten: pitch, why now, mapping to code, prompt pack index, roadmap

### Models

- `consultant-hours-invoice.tundra` upgraded (Process structure, Hours are Invoiced, extra error Scenario)
- `loan-application-entry.tundra` upgraded with Process structure; **vague Contracts kept on purpose** as a `validate-tundra` specimen
- Removed duplicate model under `examples/consultant-hours/`

### Examples

- Replaced happy-path-only demos with `demo.py` / `demo.c`
- Roles, per-subject state, correct Contract checks, three Scenarios

### Prompts

- extract / implement / validate aligned with light structure, Roles in code, and testability gates
