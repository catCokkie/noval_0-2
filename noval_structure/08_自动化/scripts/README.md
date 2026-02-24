# scripts 说明

本目录提供可运行的最小自动化脚本，目标是先打通可执行闭环，再逐步增强策略与准确率。

## 当前实现范围

- 只依赖 Python 标准库，不依赖第三方包。
- 优先覆盖固定 Schema、基础校验和可机读输出。
- YAML 解析为子集解析，适配当前仓库文件结构。

## 脚本清单

- `上下文组装.py`
  - 输入：`--chapter-id`、`--task-type`（支持 `goal/constraints/quality_target`）。
  - 输出：完整 request JSON。
  - 默认行为：按 `schemas/request.schema.json` 做严格校验。
- `一致性检查.py`
  - 输入：`--chapter-file`
  - 输出：`result/violations/foreshadow_updates`（默认 YAML-like，可加 `--json`）。
  - 默认行为：按 `schemas/chapter_front_matter.schema.json` 校验 Front Matter。
- `伏笔追踪.py`
  - 输入：`--chapter-id`
  - 输出：伏笔状态迁移建议、逾期提醒、告警。
- `成本汇总.py`
  - 输入：`--source`（默认项目驾驶舱 CSV）。
  - 输出：按章节/阶段/模型/月的成本聚合与超预算告警。
- `schema_validate.py`
  - 输入：`--kind request|response|front_matter --input <file>`
  - 输出：schema 校验结果 JSON（`valid` + `errors`）。

## Schema 文件

- `../schemas/request.schema.json`
- `../schemas/response.schema.json`
- `../schemas/chapter_front_matter.schema.json`

## 示例命令

```powershell
py "noval_structure/08_自动化/scripts/上下文组装.py" --chapter-id v01-c001 --task-type chapter_outline
py "noval_structure/08_自动化/scripts/一致性检查.py" --chapter-file "noval_structure/05_定稿层/第01卷/第001章.md"
py "noval_structure/08_自动化/scripts/schema_validate.py" --kind front_matter --input "noval_structure/05_定稿层/第01卷/第001章.md"
```
