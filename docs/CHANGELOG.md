# CHANGELOG — 变更历史日志

本文档遵循只追加（Append Only）原则，记录项目全量核心设计、架构与代码变更。

---

## [2026-09-14] - 文档：服务器 Git 部署与 dubious ownership

### 文档
- **`[issue003]`** 登记服务器 `dubious ownership` 根因与 `safe.directory` 解法。
- **`[部署]`** [`docs/DEPLOYMENT_GUIDE.md`](file:///e:/AIProject/File%20Desensitization/docs/DEPLOYMENT_GUIDE.md) 新增 §3.4：从手动上传改为 Git pull（GitHub + Gitee）；FAQ Q5/Q6。

---

## [2026-09-14] - issue002：效果对比采样与弹窗信息架构修订

### 修复 / 增强
- **`[issue002]`** 采样器改为每 Sheet **结构≤5、数据≤5**，避免多 Sheet 时后面页 Diff 为空。
- **`[issue002]`** 效果对比顶部去掉全量改名列表，改为一句「已将 N 个工作表重命名」；Sheet Tab 改为横向滚动。
- **`[文档]`** 更新 RFC004、ISSUES issue002。

### 验证
- `python -m pytest tests/ -v` 全绿；示例 18 Sheet 文件每页均有结构/数据样本。

---

## [2026-09-15] - RFC005：按 Sheet 纠错表头行（RFC003-C）

### 新增 / 增强
- **`[RFC005]`** 默认仍自动识别；新增 `header_row_overrides`，仅覆盖指定工作表的表头行。
- **`[RFC005]`** `POST /api/tasks/{id}/reprocess`：在效果对比中改某一 Sheet 行号后复用原文件重跑；支持「恢复自动识别」。
- **`[RFC005]`** 解析优先级：Sheet 纠错覆盖 > 全局 manual > 自动识别。
- **`[文档]`** 新增 [`docs/rfcs/RFC005.md`](file:///e:/AIProject/File%20Desensitization/docs/rfcs/RFC005.md)；RFC003 §8.2 C 标记已落地。

### 验证
- `python -m pytest tests/ -v` 全绿。

---

## [2026-09-15] - RFC004：效果对比分 Sheet 切换 + 结构脱敏可见

### 新增 / 增强
- **`[RFC004]`** 新增 [`backend/app/engine/rules/diff_sampler.py`](file:///e:/AIProject/File%20Desensitization/backend/app/engine/rules/diff_sampler.py)：每 Sheet 最多 8 条数据样本；`HEADER` / `SHEET` 结构样本优先、不占数据配额；全局上限 100 条。
- **`[RFC004]`** 处理结果与 Diff 接口返回 `sheet_renames`（工作表改名映射）。
- **`[RFC004]`** 前端「效果对比」改为 Tab 切换：顶部 Sheet 改名总览；每 Tab 展示表头行号、列名脱敏样本与数据样本。
- **`[RFC004]`** 新增 [`tests/test_diff_sampler.py`](file:///e:/AIProject/File%20Desensitization/tests/test_diff_sampler.py)；RFC001 §7 讨论整理进 RFC004。

### 验证
- `python -m pytest tests/ -v` 全绿。

---

## [2026-09-15] - RFC003 A+B：说明清晰 + 展示各 Sheet 表头识别结果

### 新增 / 增强
- **`[RFC003-A]`** 上传区「表头位置」文案说清：默认自动、**每个工作表单独判断**；手动指定会套用到全部工作表。
- **`[RFC003-B]`** 任务完成后带回 `header_rows`；队列列表显示简要识别结果；「效果对比」弹窗展示每个 Sheet 的表头行。
- **`[文档]`** RFC003 §8 锁定 A→B→C 路线；RFC001 末尾讨论整理完毕；「按 Sheet 单独设行号」(C) 暂缓。

### 验证
- `python -m pytest tests/ -v` 全绿。

---

## [2026-09-15] - RFC003：智能识别表头所在行（阶段 A）

### 新增 (Added)
- **`[RFC003]`** 新增 [`backend/app/engine/rules/header_detector.py`](file:///e:/AIProject/File%20Desensitization/backend/app/engine/rules/header_detector.py)：扫描前 15 行启发式识别表头；标题行降权、关键词加分、下一行数据特征加分。
- **`[RFC003]`** `ExcelProcessor` 改为按识别出的表头行处理数据与可选列名脱敏；表头上方标题区默认不脱敏。
- **`[RFC003]`** 上传 API / 前端支持 `header_row_mode=auto|manual` 与 `header_row` 手动指定。
- **`[RFC003]`** 新增 [`tests/test_header_detection.py`](file:///e:/AIProject/File%20Desensitization/tests/test_header_detection.py)（6 项）；`whats-new.js` 版本升至 `2026.09.15`。

### 验证
- `python -m pytest tests/ -v` → 26 passed。

---

## [2026-09-14] - task003：用户可见「最近更新」（方案 A+B）

### 新增 (Added)
- **`[task003]`** 顶栏「最近更新」入口 + 弹窗时间线；未读红点；新版本首次进入自动提示一次（`localStorage` 记录已读版本）。
- **`[task003]`** 新增 [`frontend/js/whats-new.js`](file:///e:/AIProject/File%20Desensitization/frontend/js/whats-new.js) 用户向更新文案（含列名/工作表可选脱敏说明）。

### 验证
- 静态资源可访问；`python -m pytest tests/ -v` → 20 passed。

---

## [2026-09-14] - task004：文档闭环与 RFC003 落盘

### 文档 (Docs)
- **`[task004]`** 更新 [`docs/excel_desensitization_solution.md`](file:///e:/AIProject/File%20Desensitization/docs/excel_desensitization_solution.md)：同步已落地的列名 / 工作表名称可选脱敏，以及顶栏「最近更新」入口。
- **`[task004]`** 更新 [`docs/README.md`](file:///e:/AIProject/File%20Desensitization/docs/README.md)：将 RFC001 / RFC002 状态改为已实施，并补充 RFC003 导航。
- **`[task004]`** 新增 [`docs/rfcs/RFC003.md`](file:///e:/AIProject/File%20Desensitization/docs/rfcs/RFC003.md)：锁定“智能识别表头所在行（阶段 A：自动识别 + 手动指定）”方案。

### 验证
- 文档路由、状态标识与变更记录人工核对通过。

---

## [2026-09-14] - issue001：修复本地 8000 端口冲突导致 Not Found

### 修复 (Fixed)
- **`[issue001]`** 本地访问 `http://127.0.0.1:8000` 仅返回 `{"detail":"Not Found"}`：根因为本机 `127.0.0.1:8000` 被其他 uvicorn / 幽灵监听占用，浏览器未打到本项目服务。
- **`[issue001]`** [`run.py`](file:///e:/AIProject/File%20Desensitization/run.py) 增加端口探测：占用且非本站时自动换端口；已运行本站则直接打开浏览器；支持环境变量 `AIMASK_PORT`。
- **`[issue001]`** [`启动工具站.bat`](file:///e:/AIProject/File%20Desensitization/启动工具站.bat) 改为调用 `run.py`，避免绕过检测。

### 文档 (Docs)
- 登记 [`.phrase/docs/ISSUES.md`](file:///e:/AIProject/File%20Desensitization/.phrase/docs/ISSUES.md) `issue001` 完整复盘；[`docs/DEPLOYMENT_GUIDE.md`](file:///e:/AIProject/File%20Desensitization/docs/DEPLOYMENT_GUIDE.md) FAQ 新增 Q4。

---

## [2026-09-14] - task002：前端结构脱敏勾选与 API 联调

### 新增 (Added)
- **`[task002]`** 上传区新增「可选：是否连表结构一起脱敏」面板：列名（表头）、工作表名称（Sheet 名）两个默认不勾选 checkbox，附通俗提示文案。
- **`[task002]`** 前端上传时提交 `mask_headers` / `mask_sheet_names`；队列表格显示「+ 列名 / + Sheet」标签；Diff 弹窗脱敏类型大白话化（如「列名脱敏」「工作表名称脱敏」）。
- **`[task002]`** 新增 [`tests/test_upload_api.py`](file:///e:/AIProject/File%20Desensitization/tests/test_upload_api.py) 验证上传 API 结构开关透传。

### 验证
- `python -m pytest tests/ -v` → 20 passed。

---

## [2026-09-14] - task001：后端支持可选列名 / Sheet 名脱敏

### 新增 (Added)
- **`[task001]`** `ExcelProcessor` 支持 `custom_options.mask_headers` / `mask_sheet_names`（默认关闭）；处理顺序为「先数据行（原始列名匹配）→ 再改列名 / Sheet 名」；Sheet 名非法字符清洗与同簿唯一化；Diff 样本增加 `HEADER` / `SHEET`。
- **`[task001]`** `/api/upload` 增加 Form 字段 `mask_headers`、`mask_sheet_names`；`TaskItem` 与任务队列透传至引擎。
- **`[task001]`** 新增 [`tests/test_structure_options.py`](file:///e:/AIProject/File%20Desensitization/tests/test_structure_options.py)：默认不改、单开、双开、跨表列名一致、Sheet 合法化、standard_mask 表头打星等 7 项用例。

### 验证
- `python -m pytest tests/ -v` → 18 passed。

---

## [2026-09-14] - 锁定 RFC001/RFC002 并开启新阶段（方案落盘，代码待实施）

### 文档 (Docs)
- **`[RFC]`** 将 [`docs/rfcs/RFC001.md`](file:///e:/AIProject/File%20Desensitization/docs/rfcs/RFC001.md) 升格为「已锁定 / 待实施」：上传前可选是否对列名、工作表名称脱敏；默认不勾选则不处理；明确「先数据后结构」与三档 Profile 对齐策略。
- **`[RFC]`** 新增 [`docs/rfcs/RFC002.md`](file:///e:/AIProject/File%20Desensitization/docs/rfcs/RFC002.md)：用户可见「最近更新」采用方案 A+B（顶栏入口 + 新版本自动提示一次）；用户向文案与开发向 CHANGELOG 分离。
- **`[阶段]`** 开启 `.phrase/phases/phase-structure-options-and-whats-new-20260914/`（spec/plan/task/change），拆解 `task001`～`task004`；更新 `.phrase/docs/CHANGE.md` 当前阶段指针与 [`docs/README.md`](file:///e:/AIProject/File%20Desensitization/docs/README.md) 路由表。

---

## [2026-08-24] - 自动脱敏工具站（Excel 专项）全套方案制定

### 新增 (Added)
- 新增 [`docs/excel_desensitization_solution.md`](file:///e:/AIProject/File%20Desensitization/docs/excel_desensitization_solution.md)：
  - **规则引擎**：分析用户初始想法并扩充为 5 层智能脱敏引擎（表头防护、高危 PII 数字精准识别、分类枚举保留、实体一致性假名化、长文本中间打星）。
  - **行业专属画像**：结合亚马逊电商利润报表（75列宽表）、FBA多国库存明细（71列）、店铺组织架构映射表等实战数据，建立电商/工厂生产/仓储/人事行政等模块专用脱敏策略库与跨表 JOIN 关联一致性保护机制。
  - **预设模式**：提供 AI 数据分析友好模式、标准字符掩码模式、深度匿名化模式三档预设。
  - **产品流程**：设计批量上传、排队处理、Diff 对比预览、单个/一键打包下载、阅后即焚生命周期。
  - **UI/UX 与架构**：设计清晰易用的现代控制台交互原型、管道化可扩展架构（支持未来 Word/PDF/JSON 扩展）与零数据驻留隐私机制。
- 新增 [`docs/README.md`](file:///e:/AIProject/File%20Desensitization/docs/README.md)：建立项目文档索引与快速查找路由表。
- **`[task001]` 阶段治理与脚手架体系初始化**：建立 `.phrase/` 体系，开启阶段 `phase-scaffold-and-core-20260824` 并落地 `spec_*`、`plan_*`、`task_*`、`change_*` 套件。
- **`[task002]` 后端脱敏引擎骨架与核心规则库搭建**：完成 FastAPI 入口、`IFileProcessor` 抽象基类、`ExcelProcessor` 核心处理管道、`NERQWEQ` $\rightarrow$ `NE***EQ` 文本中间打星算法、高危 PII 正则库、跨表一致性假名池 `PseudonymPool` 以及异步任务排队管理器 `TaskQueueManager`。
- **`[task003]` 现代化 Web 前端控制台落地**：完成 SaaS 极简控制台界面开发，涵盖策略切换卡片、批量拖拽上传、排队进度看板、Diff 效果弹窗以及打包 ZIP 下载联动。
- **`[task004]` 自动化测试套件与真实业务数据端到端联调**：建立 `pytest` 自动化测试套件，针对 `docs/Example/` 真实数据完成 11 项单元与端到端测试，验证 75 列表头保护、跨表 ASIN 假名一致性、数值完整性及打星算法 100% 通过。
- **`[优化]` 策略文案大白话通俗化升级与样式微调**：将三档脱敏策略重塑为“智能 AI 模式”、“经典打星模式”、“绝密粉碎模式”，并在前端界面完成同步更新，强制“强烈推荐”标签单行不折行展示。
- **`[功能]` 安全隐私说明弹窗上线**：在顶部右上角“零数据驻留 / 30分钟阅后即焚”徽章上增加点击弹窗交互，以标准 Q&A 形式清晰阐述 30 分钟自动兜底销毁、手动即点即焚及零数据驻留保障机制。
- **`[文档]` 内网与宝塔面板部署实战指南发布**：新增 [`docs/DEPLOYMENT_GUIDE.md`](file:///e:/AIProject/File%20Desensitization/docs/DEPLOYMENT_GUIDE.md) 及配套 `Dockerfile`，涵盖局域网 0.0.0.0 共享访问、宝塔 Python 项目管理器一键配置、Nginx 反代 100MB 大文件与 300s 超时调优方案。
- **`[工程]` 新增 Git 忽略规则清单 (`.gitignore`)**：严格屏蔽所有 `.xlsx/.xls/.csv` 业务素材数据、`docs/Example/` 样例库、`temp/` 脱敏沙箱目录、Python 虚拟环境与字节码缓存，防止任何真实敏感数据误入 Git 代码仓库。
