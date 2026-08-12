# Intentional structural defects

This model is a **negative fixture** for `tools/check_tundra.py`.  
It must **FAIL** the checker (not be used as a style reference).

```bash
python3 tools/check_tundra.py examples/bad-structure/ && echo 'unexpected OK' || echo 'expected FAIL'
```
