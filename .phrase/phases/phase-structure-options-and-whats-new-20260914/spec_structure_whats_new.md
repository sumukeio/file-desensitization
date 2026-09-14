# Phase Spec: 结构可选脱敏 + 用户可见更新记录

> **阶段标识**：`phase-structure-options-and-whats-new-20260914`  
> **启动日期**：2026-09-14  
> **状态**：🟡 进行中（方案已锁定，待按 task 实施）  
> **依据文档**：[`docs/rfcs/RFC001.md`](../../../docs/rfcs/RFC001.md)、[`docs/rfcs/RFC002.md`](../../../docs/rfcs/RFC002.md)

---

## Goals（目标）

1. 支持用户在脱敏前**自由勾选**是否对列名、工作表名称脱敏；默认不勾选则行为与现网一致。
2. 上线用户可见的「最近更新」（方案 A+B：顶栏入口 + 新版本自动提示一次），文案通俗易懂。

## Non-goals（非目标）

- 不脱敏文件名；不处理多级/合并表头的复杂语义。
- 不上 CMS、不做账号体系下的个性化公告。
- 不重构脱敏引擎架构；不扩展 Word/PDF。
- 不把 `docs/CHANGELOG.md` 直接展示给终端用户。

## 验收标准（阶段级）

1. RFC001 §6 全部满足，且默认关闭路径有回归测试保护。
2. RFC002 §7 全部满足，示例文案已写入用户向数据源。
3. `docs/excel_desensitization_solution.md`、`docs/CHANGELOG.md`、本阶段 `change_*.md` 已按规范回写。
4. 每个 `taskNNN` 完成后强制刹车，经人类确认后再进入下一任务。
