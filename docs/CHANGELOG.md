# CHANGELOG — 变更历史日志

本文档遵循只追加（Append Only）原则，记录项目全量核心设计、架构与代码变更。

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
