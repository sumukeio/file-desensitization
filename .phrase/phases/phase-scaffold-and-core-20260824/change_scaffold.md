# Phase Changes: 项目脚手架搭建与核心脱敏引擎基础 (phase-scaffold-and-core-20260824)

本文档按时间倒序记录本阶段所有已完成原子任务的具体变更详情。

---

## 变更记录

### [2026-08-24] - task004: 编写自动化测试套件并针对真实样例数据完成联调验证
- **任务编号**：`task004`
- **变更摘要**：
  - 编写 `tests/test_maskers.py`（针对文本中间打星 `NERQWEQ` $\rightarrow$ `NE***EQ`、手机号、身份证号、邮箱等断言）；
  - 编写 `tests/test_pseudonym.py`（针对实体假名池同值同代号、跨类别隔离及重置机制进行断言）；
  - 编写 `tests/test_example_files.py`（加载 `docs/Example/` 下真实 75 列亚马逊利润表、71 列 FBA 库存表及店铺映射表，断言表头保护、跨表 ASIN/店铺假名一致性及数值完整性）；
  - 创建 `pytest.ini` 并优化前端 `.tag-recommend` 样式强制单行展示。
- **验证凭据**：
  - 执行 `pytest tests/ -v`，11 个测试用例 100% 全部 PASSED。

### [2026-08-24] - task003: 搭建现代化 Web 前端控制台脚手架
- **任务编号**：`task003`
- **变更摘要**：
  - 创建 `frontend/index.html`（现代化 SaaS 控制台：三档策略切换卡片、多文件拖拽上传 Dropzone、排队看板、Diff 效果弹窗）；
  - 创建 `frontend/css/style.css`（规范 CSS 变量、响应式布局、状态徽章、进度条动效与高亮对比样式）；
  - 创建 `frontend/js/app.js`（实现策略选择绑定、多文件拖拽上传、1秒动态排队轮询渲染、Diff 弹窗交互及打包 ZIP 下载触发）；
  - 在 `backend/app/main.py` 中挂载前端静态资源。
- **验证凭据**：
  - 自动化端点测试校验：`/` (200 OK), `/css/style.css` (200 OK), `/js/app.js` (200 OK), `/api/tasks` (200 OK)。

### [2026-08-24] - task002: 搭建后端 Python 脱敏引擎架构骨架与核心接口
- **任务编号**：`task002`
- **变更摘要**：
  - 创建 `backend/` 完整模块架构（`core/`, `schemas/`, `engine/`, `api/`）；
  - 实现 `IFileProcessor` 插件化抽象基类及 `ExcelProcessor` 核心处理管道；
  - 实现 `mask_text_middle`（精准满足 `NERQWEQ` $\rightarrow$ `NE***EQ` 规则）、`detect_and_mask_pii` 正则识别库与 `PseudonymPool` 全局跨表一致性假名池；
  - 实现异步任务排队管理器 `TaskQueueManager` 与 FastAPI 端点路由（`/api/upload`, `/api/tasks`, `/api/tasks/{id}/diff`, `/api/tasks/{id}/download`, `/api/download-all`）。
- **验证凭据**：
  - 运行单元测试断言，验证文本中间打星、手机号掩码及实体假名化映射 100% 通过。

### [2026-08-24] - task001: 初始化 .phrase/ 治理体系与规范配置
- **任务编号**：`task001`
- **变更摘要**：
  - 建立 `.phrase/docs/` 变更总索引 `CHANGE.md`、缺陷追踪 `ISSUES.md` 及体系说明 `README.md`；
  - 创建首个阶段 `phase-scaffold-and-core-20260824` 及其四件套（`spec_scaffold.md`, `plan_scaffold.md`, `task_scaffold.md`, `change_scaffold.md`）；
  - 同步更新全局 [`docs/CHANGELOG.md`](file:///e:/AIProject/File%20Desensitization/docs/CHANGELOG.md)。
- **验证凭据**：
  - `.phrase/` 文件结构完备，路径索引无死链；
  - 严格符合 [`docs/AGENTS.md`](file:///e:/AIProject/File%20Desensitization/docs/AGENTS.md) 治理规范。
