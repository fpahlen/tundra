# models/

Put **your** Tundra translations here (any regulation or domain slice).

This directory is intentionally empty of house samples so the core product is not tied to one instrument.

| Convention | Path |
| --- | --- |
| Your translations | `models/*.tundra` |
| House samples (any instrument) | [`../examples/regulations/`](../examples/regulations/) |
| Working excerpts in an app | `sources/<instrument>/` (create as needed) |

```bash
python3 tools/check_tundra.py models/
```
