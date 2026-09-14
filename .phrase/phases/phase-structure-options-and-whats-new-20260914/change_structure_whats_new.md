# Phase Change Log: 结构可选脱敏 + 用户可见更新记录

> 时间倒序追加。仅在对应 `taskNNN` 完成并验证后写入。

---

## 2026-09-14 — `task003` 完成：「最近更新」方案 A+B

- **变更摘要**：
  - 顶栏新增「最近更新」徽章（未读红点）；弹窗展示用户向时间线（`whats-new.js`）。
  - 未读新版本首次进入自动弹出一次；点「知道了」写入 `localStorage` 并清除红点；可手动回看历史。
  - 文案含列名/工作表可选脱敏说明，无技术黑话。
- **验证凭据**：`http://127.0.0.1:8001/js/whats-new.js` 200；`pytest` 20 passed。
- **状态**：等待人类确认后进入 `task004`。

---

## 2026-09-14 — `task004` 完成：文档闭环与 RFC003 落盘

- **变更摘要**：
  - 更新 `docs/excel_desensitization_solution.md`，将已落地的「列名/工作表名称可选脱敏」与「最近更新」入口同步进产品主方案。
  - 更新 `docs/README.md`，将 RFC001 / RFC002 状态改为已实施，并补充 RFC003 导航。
  - 新增 `docs/rfcs/RFC003.md`，锁定“自动识别表头所在行（阶段 A：自动识别 + 手动指定）”方案。
- **验证凭据**：
  - 文档链接与状态人工核对完成；
  - `docs/CHANGELOG.md` 仅追加，无覆盖历史。
- **状态**：本阶段 `task001`～`task004` 全部完成；后续若继续实现表头智能识别，建议另开新 task / 新阶段承接 RFC003。

---

## 2026-09-14 — `task002` 完成：前端勾选与 API 联调

- **变更摘要**：
  - 上传区新增「可选：是否连表结构一起脱敏」面板，含列名 / Sheet 名两个默认不勾选 checkbox 及通俗提示。
  - `app.js` 上传时提交 `mask_headers` / `mask_sheet_names`；队列表格显示结构脱敏标签；Diff 弹窗脱敏类型大白话化。
  - 新增 `tests/test_upload_api.py` 验证 API 默认 false 与 true 透传。
- **验证凭据**：`python -m pytest tests/ -v` → **20 passed**（约 2.16s）。
- **状态**：等待人类确认后进入 `task003`。

---

## 2026-09-14 — `task001` 完成：后端可选列名 / Sheet 名脱敏

- **变更摘要**：
  - `ExcelProcessor`：`custom_options.mask_headers` / `mask_sheet_names`（默认 false）；先数据行后结构；Sheet 名清洗与唯一化；Diff 增加 `HEADER` / `SHEET` 样本。
  - `/api/upload`：新增 Form 字段 `mask_headers`、`mask_sheet_names`；`TaskItem` 与队列透传至引擎。
  - 新增 `tests/test_structure_options.py`（7 项）。
- **验证凭据**：`python -m pytest tests/ -v` → **18 passed**（约 1.19s）。
- **状态**：等待人类确认后进入 `task002`。

---

## 2026-09-14 — 阶段开启与方案落盘（尚未进入代码实施）

- **事件**：人类确认 RFC001（列名/Sheet 可选脱敏）与 RFC002（最近更新 A+B）设计；开启本阶段并落盘四件套。
- **产出文档**：
  - [`docs/rfcs/RFC001.md`](../../../docs/rfcs/RFC001.md) → 状态改为「已锁定 / 待实施」
  - [`docs/rfcs/RFC002.md`](../../../docs/rfcs/RFC002.md) → 新建并锁定
  - 本目录 `spec_*` / `plan_*` / `task_*` / `change_*`
- **下一动作**：等待人类确认后执行 **`task001`**（后端引擎 + API）。
