# 接口与 Schema 变更说明

## 1. 保持不变

以下主契约保持与 `noval_structure` 一致：

- 章节 Front Matter Schema：`08_自动化/schemas/chapter_front_matter.schema.json`
- 请求包 Schema：`08_自动化/schemas/request.schema.json`
- 响应包 Schema：`08_自动化/schemas/response.schema.json`
- 人物卡、伏笔账本、章节字段命名保持原有英文键。

## 2. 新增内部治理接口

### 审阅优先级矩阵

文件：`01_项目驾驶舱/审阅优先级矩阵.csv`

字段：

- `id`
- `path`
- `reader_score`
- `editor_score`
- `author_score`
- `priority`
- `status`
- `notes`

### 来源追溯表

文件：`00_源方案分析/来源映射表.csv`

字段：

- `claim_id`
- `source_file`
- `target_path`
- `decision`
- `confidence`

### 三视角归并台账

文件：`00_源方案分析/三视角归并台账.csv`

字段：

- `claim_id`
- `source_file`
- `claim`
- `reader_score`
- `editor_score`
- `author_score`
- `adopt_decision`
- `target_path`

## 3. 重要度模型

- 加权：编辑 0.45、读者 0.35、作者 0.20。
- 分层：P0 >= 85；P1 70-84；P2 < 70。
- 涉及硬规则、世界观主干、主角动机、主线伏笔的条目至少为 P1。

