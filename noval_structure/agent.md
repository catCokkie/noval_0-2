# agent.md - AI 交互准则（小说协作项目）

## 1. 适用范围与角色说明

本规范用于 `noval_structure` 下的 AI 协作任务，覆盖四类角色：

- 架构师：维护宪法、规则、卷纲、风险控制。
- 叙事者：生成章纲、场景骨架、正文草稿。
- 监察官：执行一致性、伏笔、成本与质量校验。
- 润色师：在不改动关键事实前提下统一文风。

## 2. 输入优先级与上下文加载顺序

固定加载顺序：

1. `01_项目驾驶舱/作品宪法.md`
2. `02_正史资产_Canon/规则/硬规则_R1-R3.md`
3. 当前章相关人物卡
4. 上一章摘要（或反向总纲最近段）
5. `02_正史资产_Canon/伏笔账本.yml`
6. 当前任务提示词（`07_提示词合约/*.md`）

冲突处理：高优先级输入覆盖低优先级输入。

## 3. 请求包 Schema

```yaml
request:
  task_type: "chapter_outline|scene_skeleton|draft_expand|continuity_check"
  chapter_id: "v01-c001"
  goal: "本次任务目标"
  must_keep: []
  forbidden: []
  inputs:
    constitution: "摘要或路径"
    hard_rules: "摘要或路径"
    character_states: []
    previous_summary: "上一章摘要"
    foreshadow_state: []
  constraints:
    word_count_target: 2000
    pov: "林逸"
    new_terms_budget: 1
    hook_type: "信息钩子"
  quality_target:
    consistency_score_min: 90
    style_alignment_min: 85
```

必填字段：`task_type`, `chapter_id`, `goal`, `inputs`, `constraints`, `quality_target`。

严格校验文件：`08_自动化/schemas/request.schema.json`。

## 4. 响应包 Schema

```yaml
response:
  summary: "执行结果摘要"
  content: "正文或结构化内容"
  consistency_flags: []
  foreshadow_updates: []
  cost_record:
    model_used: "gpt-4.1"
    token_in: 3200
    token_out: 2100
    cost_usd: 0.16
  next_actions: []
```

必填字段：`summary`, `content`, `consistency_flags`, `foreshadow_updates`, `cost_record`, `next_actions`。

严格校验文件：`08_自动化/schemas/response.schema.json`。

## 5. 四阶段执行协议

- Canon：新设定先入 Canon，再进入 Planning/Draft。
- Planning：章纲聚焦“本章改变了什么”，不提前锁死细节。
- Draft：按章纲 -> 场景骨架 -> 正文扩写执行。
- Validation：先章节级，再季度级，未通过不得推进状态。

## 6. 章节级质量门禁

每章必须通过以下检查：

1. 因果完整
2. 规则合规
3. 角色一致
4. 线索可追
5. 代价存在
6. 术语受控
7. 伏笔登记完整
8. 钩子单一
9. 成本字段完整

## 7. Canon 变更协议

- 新核心设定不得直接进正文。
- 变更流程：提出变更 -> 标注影响章节 -> 审批 -> 更新 Canon -> 同步章纲/正文。
- `last_updated_chapter` 必须更新到对应人物卡。

## 8. 成本与模型路由准则

- 以 `08_自动化/模型路由与成本.yml` 为唯一来源。
- 若输出不达质量阈值，按 `escalation_rule` 升级或回退模型。
- `cost_record` 缺失视为流程失败，不得标记通过。

## 9. 禁行项

- 未入 Canon 的关键设定直接写入正文。
- 人物 OOC 且无解释。
- 无代价升级。
- 伏笔埋设或回收不登记。
- 成本字段缺失仍标记通过。

## 10. 快速交互模板

### 10.1 章纲生成

```yaml
task_type: chapter_outline
chapter_id: v01-c001
goal: 生成第001章章纲
constraints:
  pov: 林逸
  word_count_target: 0
  new_terms_budget: 1
  hook_type: 信息钩子
```

### 10.2 场景骨架

```yaml
task_type: scene_skeleton
chapter_id: v01-c001
goal: 将章纲扩展为3-6个场景骨架
```

### 10.3 正文扩写

```yaml
task_type: draft_expand
chapter_id: v01-c001
goal: 产出约2000字正文草稿
```

### 10.4 连续性检查

```yaml
task_type: continuity_check
chapter_id: v01-c001
goal: 输出违规项和修复建议
```

