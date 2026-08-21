# 遗留手工联调脚本

这些 `test_*.py` 曾放在 `backend/` 根目录，依赖真实库/服务，**不是** pytest 正式套件。

正式单测请用：

```bash
cd backend
python -m pytest tests/unit -q --tb=short
```

本目录已被 `pyproject.toml` 的 `norecursedirs` 与 `.dockerignore` 排除。需要某条场景时再手工运行对应脚本。
