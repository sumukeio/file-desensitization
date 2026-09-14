# Phase Tasks: 结构可选脱敏 + 用户可见更新记录

> 严格遵循单任务原子推进：每完成一项并验证后，必须停下等待人类确认。

---

## 任务清单

- [x] **`task001`**: 后端可选列名 / Sheet 名脱敏（引擎 + API + 队列透传）
  - **产出**：
    - `ExcelProcessor` 支持 `mask_headers` / `mask_sheet_names`（默认 false）
    - 处理顺序：先数据行（用原始列名匹配），再按开关改写列名 / Sheet 名
    - Sheet 名合法化与同簿唯一化
    - `/api/upload` Form 接收两布尔字段；`queue` 传入 `custom_options`
    - 单元/集成测试：默认不改、单开、双开、实体匹配不被破坏
  - **验证**：`pytest tests/ -v` → **18 passed**（含新增 `tests/test_structure_options.py` 7 项）
  - **影响范围**：`backend/app/engine/excel_processor.py`、`endpoints.py`、`queue.py`、`schemas/task.py`、`tests/`
  - **依据**：[`docs/rfcs/RFC001.md`](../../../docs/rfcs/RFC001.md)
  - **完成日期**：2026-09-14

- [x] **`task002`**: 前端上传前勾选「列名 / 工作表名称」脱敏并联调
  - **产出**：
    - 上传区附近两个默认不勾选的 checkbox + 通俗提示文案
    - `FormData` 提交 `mask_headers` / `mask_sheet_names`
    - 队列表格展示「+ 列名 / + Sheet」标签；Diff 弹窗显示「列名脱敏 / 工作表名称脱敏」
    - 新增 `tests/test_upload_api.py` 验证 API 透传
  - **验证**：`python -m pytest tests/ -v` → **20 passed**
  - **影响范围**：`frontend/index.html`、`frontend/js/app.js`、`frontend/css/style.css`、`tests/test_upload_api.py`
  - **依赖**：`task001` 完成并经人类确认
  - **依据**：[`docs/rfcs/RFC001.md`](../../../docs/rfcs/RFC001.md)
  - **完成日期**：2026-09-14

- [x] **`task003`**: 「最近更新」方案 A+B 落地
  - **产出**：
    - 顶栏「最近更新」入口 + 弹窗时间线（A）
    - 新版本首次自动弹出一次 + `localStorage` 已读版本 / 红点（B）
    - `frontend/js/whats-new.js` 用户向文案，含 RFC001 能力说明
  - **验证**：静态资源 200；`pytest` 20 passed；未读自动弹一次 / 点「知道了」写 localStorage / 入口可回看历史
  - **影响范围**：`frontend/index.html`、`css/style.css`、`js/app.js`、新建 `js/whats-new.js`
  - **依赖**：建议在 `task002` 之后，以便文案与真实功能同步上线
  - **依据**：[`docs/rfcs/RFC002.md`](../../../docs/rfcs/RFC002.md)
  - **完成日期**：2026-09-14

- [x] **`task004`**: 文档与变更闭环回写
  - **产出**：
    - 更新 [`docs/excel_desensitization_solution.md`](../../../docs/excel_desensitization_solution.md) 中结构保护 / UI 相关描述（注明可选开关与「最近更新」入口）
    - 更新 [`docs/README.md`](../../../docs/README.md) 中 RFC 状态与导航
    - 新增 [`docs/rfcs/RFC003.md`](../../../docs/rfcs/RFC003.md)，锁定“自动识别表头所在行（阶段 A）”方案
    - 在 `docs/CHANGELOG.md` 追加本阶段文档闭环摘要
    - 本阶段 `change_structure_whats_new.md` 追加任务完成记录
  - **验证**：链接可点、状态标识正确、CHANGELOG 只追加不覆盖；RFC001/RFC002 状态与现状一致
  - **影响范围**：`docs/`、`.phrase/phases/.../change_*.md`
  - **依赖**：`task001`～`task003` 均完成并经人类确认
  - **完成日期**：2026-09-14
