# ISSUES.md — 缺陷与问题追踪索引

本文档用于追踪项目开发与运行过程中发现的缺陷（Issue）、技术债务与待办改进项。

---

## 缺陷与问题登记表

| 编号 | 登记日期 | 关联 Phase / Task | 严重等级 | 问题描述 | 状态 | 解决方案 / 闭环 |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| [`issue001`](#issue001--本地访问-8000-返回-detailnot-found) | 2026-09-14 | `phase-structure-options-and-whats-new-20260914` | P1 阻塞本地使用 | 本地打开 `http://127.0.0.1:8000` 只显示 `{"detail":"Not Found"}` | ✅ 已闭环 | 见下方详情；`run.py` / `启动工具站.bat` 增加端口冲突检测与自动换端口 |
| [`issue002`](#issue002--效果对比后半-sheet-无数据--弹窗信息过载) | 2026-09-14 | RFC004 | P1 体验/正确性 | 多 Sheet 勾选结构脱敏后，从第 6 个 Sheet 起 Diff 无数据；顶部改名列表过长 | ✅ 已闭环 | 每 Sheet 结构≤5、数据≤5；顶部改名改为一句摘要；Tab 横向滚动 |
| [`issue003`](#issue003--服务器-git-报-dubious-ownership) | 2026-09-14 | 宝塔部署 / Git 拉取 | P2 阻塞服务器 pull | `fatal: detected dubious ownership in repository` | ✅ 已闭环 | `git config --global --add safe.directory <项目路径>`；可选修正目录属主 |

---

## issue001 — 本地访问 8000 返回 `{"detail":"Not Found"}`

### 现象

- 已执行 `python run.py` 或 `启动工具站.bat`，控制台显示服务已启动。
- 浏览器访问 `http://127.0.0.1:8000`（或自动打开的页面）只看到：

```json
{"detail":"Not Found"}
```

- 访问 `/docs` 有时能开（说明连上了某个 FastAPI），但本站首页与 `/api/tasks` 仍 404。

### 根因

**不是前端没挂载，而是浏览器打到了「错误的监听进程」。**

排查时本机同时存在：

| 绑定 | 进程命令行（示例） | 结果 |
| :--- | :--- | :--- |
| `0.0.0.0:8000` | 本项目 `python run.py` → `backend.app.main:app` | 局域网 IP 访问正常（如 `http://10.x.x.x:8000`） |
| `127.0.0.1:8000` | 其他项目 `uvicorn api.main:app --reload`，或已退出但仍残留的「幽灵监听」 | 本机 `127.0.0.1` 优先打到这里 → FastAPI 默认 404 JSON |

补充说明：

1. Windows 上若 `0.0.0.0:8000` 与 `127.0.0.1:8000` 同时存在，访问 **localhost / 127.0.0.1** 往往打到更具体的 `127.0.0.1` 绑定。
2. 可能出现 netstat 仍显示 LISTENING、但 `taskkill` 提示进程不存在的「幽灵端口」；本机若有 Clash / VPN TUN（常见出现 `198.18.x.x` 网卡），更容易踩坑。
3. 用 TestClient 直接加载 `backend.app.main:app` 时，`/` 与 `/api/tasks` 均为 200 —— 证明应用代码本身正常。

### 验证手段（当时）

```text
# 本项目应用对象（内存中）→ 正常
GET /           200
GET /api/tasks  200

# 真实浏览器/本机 127.0.0.1 → 异常
GET http://127.0.0.1:8000/           404 {"detail":"Not Found"}
GET http://127.0.0.1:8000/api/tasks  404

# 走局域网网卡 IP → 正常（命中本项目 0.0.0.0 监听）
GET http://10.10.19.126:8000/api/tasks  200
```

### 解决方案（已落地）

1. **立刻恢复可用**
   - 关掉占用 8000 的其他 uvicorn / 旧进程：`netstat -ano | findstr ":8000"` → `taskkill /PID <PID> /F`
   - 或临时用局域网 IP 访问本项目（确认服务其实已起来）
   - 或换端口：`set AIMASK_PORT=8001` 后执行 `python run.py`
2. **工程加固**（已改代码）
   - [`run.py`](../../run.py)：启动前探测 `127.0.0.1:端口`；若被**非本站**服务占用，自动向后寻找空闲端口并打印真实地址；若本站已在跑则直接打开浏览器。
   - [`启动工具站.bat`](../../启动工具站.bat)：改为调用 `python run.py`，避免绕过检测；启动失败时提示可手动设 `AIMASK_PORT`。
3. **文档**：本 Issue + [`docs/DEPLOYMENT_GUIDE.md`](../../docs/DEPLOYMENT_GUIDE.md) FAQ 增加对应条目。

### 用户侧自检口诀

1. 看控制台打印的**真实端口**（可能不是 8000）。
2. 打开 `http://127.0.0.1:<端口>/api/tasks`，应返回带 `tasks` 字段的 JSON，而不是 `Not Found`。
3. 若仍异常：查端口占用 → 结束无关进程 → 再启动；或设置 `AIMASK_PORT` 换端口。

### 状态

✅ **已闭环**（2026-09-14）：根因确认；启动脚本加固；文档落盘。

---

## issue002 — 效果对比后半 Sheet 无数据 + 弹窗信息过载

### 现象

用 [`docs/Example/店铺和团队销售额和利润情况.xlsx`](../../docs/Example/店铺和团队销售额和利润情况.xlsx) 测试（勾选列名 + 工作表名称脱敏）：

- 从 **2603团队（第 6 个 Sheet）** 起，「数据单元格变更」为空
- 弹窗顶部列出全部 18 行「原名 → 新名」，噪音大、难用

### 根因

RFC004 初版采样器：结构样本不限量 + 全局硬上限 100。  
前几个 Sheet 的 HEADER（每表十余列）+ 数据样本吃满 100 后，后续 Sheet 的 `add()` 全部失败。文件本身仍有脱敏（`masked_count` 正常），只是对比抽样被挤爆。

### 解决方案（已落地）

1. **采样**：每 Sheet 结构（HEADER/SHEET）≤ **5**，数据 ≤ **5**；两类互不占用；软全局上限提高到 2000。
2. **UI**：去掉全量改名列表，改为「已将 N 个工作表重命名」；Tab 横向滚动 + 当前高亮，改名看 Tab 副标题。
3. **文档**：更新 [`docs/rfcs/RFC004.md`](../../docs/rfcs/RFC004.md)。

### 状态

✅ **已闭环**（2026-09-14）

---

## issue003 — 服务器 Git 报 `dubious ownership`

### 现象

在宝塔服务器项目目录执行 `git remote` / `git pull` 等命令时：

```text
fatal: detected dubious ownership in repository at '/www/wwwroot/file-desensitization'
To add an exception for this directory, call:

        git config --global --add safe.directory /www/wwwroot/file-desensitization
```

### 根因

Git 2.35.2+ 的安全策略：若**仓库目录属主**与**当前执行 git 的用户**不一致，默认拒绝操作，防止误用他人可控目录。

常见场景：目录属主是 `www`（或首次手动上传时的用户），你却用 `root` 在 SSH 里操作 git。

### 解决方案

**立刻解除拦截（推荐先做）：**

```bash
git config --global --add safe.directory /www/wwwroot/file-desensitization
```

然后再执行 `git remote add` / `git pull` 等。

**可选加固（减少以后再踩坑）：**

```bash
# 按宝塔实际运行用户调整，常见 www
chown -R www:www /www/wwwroot/file-desensitization
```

若服务用 `www`、日常用 `root` 管代码：每次 root 操作前保留 `safe.directory` 即可；或 `su - www` 后再 `git pull`。

### 关联文档

服务器从「手动上传」改为「Git pull」的完整步骤见  
[`docs/DEPLOYMENT_GUIDE.md` §3.4](../../docs/DEPLOYMENT_GUIDE.md)。

### 状态

✅ **已闭环**（2026-09-14）：根因与处理命令落盘。

### 续：首次接上 Gitee 后的正常状态（已验证）

服务器执行 `safe.directory` → `remote add gitee` → `fetch` → `checkout -f main` 后：

```text
位于分支 main
您的分支与上游分支 'gitee/main' 一致。

未跟踪的文件:
        <哈希>_venv/
```

**解读**：代码已与 Gitee `main` 对齐，流程成功。  
`<哈希>_venv/` 是宝塔 Python 项目管理器自动创建的虚拟环境，**应保留、不要 `git add`**。仓库 `.gitignore` 已增加 `*_venv/` 忽略规则。

后续日常：`git pull gitee main` → 必要时重装依赖 → 宝塔重启项目。
