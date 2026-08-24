# .phrase 体系说明文档

`.phrase/` 是本项目采用的精细化研发管理与阶段生命周期治理体系，旨在确保所有代码与架构演进具备 100% 确定性、可溯源性与可验证性。

---

## 目录结构说明

```text
.phrase/
  docs/
    CHANGE.md       # 变更总索引，顶部维护【当前进行阶段】链接
    ISSUES.md       # 缺陷与问题追踪索引 (issueNNN)
    README.md       # .phrase 体系说明
  phases/
    phase-<purpose>-<YYYYMMDD>/
      spec_*.md     # 阶段目标、范围定义 (Goals & Non-goals)、验收标准
      plan_*.md     # 里程碑计划、架构边界、风险预案
      task_*.md     # 原子任务清单 (taskNNN)，包含：产出 + 验证方式 + 影响范围
      change_*.md   # 任务完成后的变更回溯日志 (时间倒序)
      tech-refer_*.md (可选) 技术选型与规范参考
      adr_*.md        (可选) 架构决策记录
```

## 执行铁律
1. **严格单任务推进**：任务按 `task001~taskNNN` 原子化推进，每个任务完成后强制刹车等待人类确认；
2. **文档闭环同步**：任务完成后必须同步更新 `task_*.md`、`change_*.md` 与 `docs/CHANGELOG.md`；
3. **可验证交付**：所有代码变更必须附带真实可复现的验证凭据。
