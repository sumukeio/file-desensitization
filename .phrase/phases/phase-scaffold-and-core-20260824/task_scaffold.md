# Phase Tasks: 项目脚手架搭建与核心脱敏引擎基础 (phase-scaffold-and-core-20260824)

> 严格遵循单任务原子推进原则，每次完成一项并验证后，必须停下等待人类确认。

---

## 任务清单

- [x] **`task001`**: 初始化 `.phrase/` 阶段治理体系与规范配置
  - **产出**：`.phrase/` 文档索引与阶段四件套（`spec_*`, `plan_*`, `task_*`, `change_*`）
  - **验证**：文件树完整性校验与死链检查
  - **影响范围**：`.phrase/`, `docs/CHANGELOG.md`

- [x] **`task002`**: 搭建后端 Python 脱敏引擎架构骨架与核心接口
  - **产出**：`backend/` 目录、FastAPI 应用入口、IFileProcessor 管道接口、5层脱敏规则与跨表假名池
  - **验证**：Python 模块可正常 import，FastAPI 路由与规则断言 100% 通过
  - **影响范围**：`backend/`

- [x] **`task003`**: 搭建现代化 Web 前端控制台脚手架
  - **产出**：`frontend/` 目录、SaaS 极简控制台（拖拽上传、排队监控、Diff 对比弹窗、下载）
  - **验证**：静态页面结构与交互事件响应正常，FastAPI 静态挂载 200 OK
  - **影响范围**：`frontend/`

- [x] **`task004`**: 编写自动化测试套件并针对真实样例数据完成联调验证
  - **产出**：`tests/` 测试集，针对 `docs/Example/` 真实 Excel 文件的脱敏与跨表一致性断言
  - **验证**：`pytest tests/ -v` 11 项单元与端到端测试 100% 全部通过
  - **影响范围**：`tests/`
