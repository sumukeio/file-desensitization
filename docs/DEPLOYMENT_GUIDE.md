# 自动文件脱敏工具站 — 内网与宝塔面板部署实战指南

> **文档状态**：`[权威/现行]`  
> **适用环境**：本地局域网（Windows/Mac/Linux）及 内网 Linux 服务器（宝塔面板 BT-Panel）  
> **服务架构**：FastAPI 后端 + openpyxl 计算引擎 + 原生极简 Web 前端（一体化内置挂载）

---

## 目录
- [一、 部署前准备与项目打包](#一-部署前准备与项目打包)
- [二、 场景一：本地局域网一键运行 (Windows / Linux)](#二-场景一本地局域网一键运行-windows--linux)
- [三、 场景二：宝塔面板 (BT-Panel) 生产环境标准部署](#三-场景二宝塔面板-bt-panel-生产环境标准部署)
  - [3.1 方式 A：宝塔“Python 项目管理器”一键部署（推荐）](#31-方式-a宝塔python-项目管理器一键部署推荐)
  - [3.2 关键配置：Nginx 反向代理与大文件上传限制](#32-关键配置nginx-反向代理与大文件上传限制)
  - [3.3 方式 B：Docker 容器化部署（备选）](#33-方式-bdocker-容器化部署备选)
- [四、 内网自动化运维与沙箱定时清理](#四-内网自动化运维与沙箱定时清理)
- [五、 常见问题排查 (FAQ)](#五-常见问题排查-faq)

---

## 一、 部署前准备与项目打包

### 1.1 代码打包清单
在将项目上传到内网服务器前，请打包以下核心文件（排除虚拟环境 `.venv`、`.pytest_cache` 及临时文件）：

```text
File Desensitization/
├── backend/                   # 后端核心代码与引擎
│   ├── app/
│   │   ├── api/
│   │   ├── core/
│   │   ├── engine/
│   │   ├── schemas/
│   │   └── main.py            # FastAPI 服务入口
├── frontend/                  # 前端静态页面
│   ├── css/
│   ├── js/
│   └── index.html
├── requirements.txt           # Python 依赖清单（置于根目录，宝塔自动识别）
├── 启动工具站.bat              # Windows 本地双击启动脚本
├── run.py                     # Python 跨平台启动入口
└── pytest.ini                 # 测试配置
```

---

## 二、 场景一：本地局域网一键运行 (Windows / Linux)

如果您希望在自己的电脑或内网某台办公 PC 上直接启动，让局域网内的同事也能访问：

### 2.1 依赖安装
打开终端（PowerShell 或 CMD），进入项目根目录：
```powershell
pip install -r backend/requirements.txt
```

### 2.2 允许局域网其他电脑访问
默认的 `启动工具站.bat` 绑定的是 `127.0.0.1`（仅本机可访问）。若需**局域网共享**，请使用以下命令将监听地址设为 `0.0.0.0`：

```powershell
python -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000
```

### 2.3 局域网同事访问
1. 查询您的电脑在内网的 IP（Windows 执行 `ipconfig`，例如 `192.168.1.100`）；
2. 局域网内其他同事直接在浏览器访问：  
   👉 **`http://192.168.1.100:8000`**
3. **注意**：Windows 防火墙若弹出提示，请勾选“允许专用网络访问”；或在 Windows 防火墙添加入站规则放行 `8000` 端口。

---

## 三、 场景二：宝塔面板 (BT-Panel) 生产环境标准部署

在内网 Linux 服务器（CentOS / Ubuntu / Debian）安装了宝塔面板的环境下，推荐使用宝塔自带的 **Python 项目管理器** 进行守护进程化部署。

---

### 3.1 方式 A：宝塔“Python 项目管理器”一键部署（推荐）

#### 第 1 步：安装 Python 项目管理器插件
1. 登录宝塔面板后台 $\rightarrow$ 进入 **【软件商店】**；
2. 搜索 `Python项目管理器` 并点击安装（推荐安装 2.0 以上版本）。

#### 第 2 步：上传项目文件
1. 进入宝塔 **【文件】** 菜单；
2. 在网站根目录（如 `/www/wwwroot/`）下新建文件夹 `file-desensitization`；
3. 将项目完整代码上传解压至 `/www/wwwroot/file-desensitization`。

#### 第 3 步：在 Python 项目管理器中添加项目
1. 打开 **【Python 项目管理器】** $\rightarrow$ 点击 **【版本管理】**，安装 **Python 3.10** 或更高版本（如 3.11 / 3.12）；
2. 切换到 **【项目管理】** $\rightarrow$ 点击 **【添加项目】**：
   - **项目名称**：`excel-desensitizer`
   - **项目路径**：选择 `/www/wwwroot/file-desensitization`
   - **Python 版本**：选择刚才安装的 `Python 3.11+`
   - **框架**：选择 `python`
   - **启动方式**：选择 `python`（最稳妥零报错）
   - **启动文件**：选择 `/www/wwwroot/file-desensitization/run.py`
   - **运行参数**：留空
   - **运行用户**：推荐选择 **`root`**（避免因 `logs/` 或 `temp/` 目录缺少写权限导致启动失败）
   - **开机启动**：勾选 ✅
   - **守护进程**：**建议先不勾选**（除非在宝塔软件商店中已安装过【Supervisor 进程守护管理器】插件，否则勾选会报插件未安装错误）
3. 点击 **【确定】**，宝塔将自动完成环境构建并启动服务。

#### 第 4 步：安装依赖模块
1. 在项目列表中，找到刚创建的项目，点击右侧的 **【模块】**；
2. 点击 **【从 requirements.txt 安装】**，选择项目中的 `backend/requirements.txt`；
3. 等待宝塔自动安装 `fastapi`, `uvicorn`, `openpyxl`, `pydantic`, `python-multipart` 完成；
4. 返回项目列表，点击 **【重启】** 项目，状态显示为绿色 **运行中** 即表示启动成功。

---

### 3.2 关键配置：Nginx 反向代理与大文件上传限制

为了让用户直接通过内网域名或标准 80/443 端口访问，并且防止大 Excel 处理超时，需要在宝塔中配置 Nginx：

#### 1. 新建站点
1. 宝塔后台 $\rightarrow$ **【网站】** $\rightarrow$ **【添加站点】**；
2. 填写内网域名（如 `desensitize.internal.com`）或直接绑定服务器内网 IP + 独立端口（如 `192.168.1.200:80`）；
3. 根目录任意选择，PHP版本选择 **纯静态**。

#### 2. 配置反向代理
进入站点设置 $\rightarrow$ **【反向代理】** $\rightarrow$ **【添加反向代理】**：
- **代理名称**：`desensitize-api`
- **目标 URL**：`http://127.0.0.1:8000`
- **发送域名**：`$host`

#### 3. 调整 Nginx 配置（防超时与突破上传上限）
点击站点设置中的 **【配置文件】**，在 `server { ... }` 块中加入以下三行关键调优参数：

```nginx
# 1. 允许上传最大 100MB 的 Excel/CSV 文件
client_max_body_size 100m;

# 2. 调大处理超时时间（防止几十兆大表格计算脱敏时出现 504 Gateway Time-out）
proxy_connect_timeout 300s;
proxy_read_timeout 300s;
proxy_send_timeout 300s;

# 3. 开启支持流式下载与实时排队状态透传
proxy_buffering off;
```
保存并重载 Nginx。此时在内网浏览器输入域名或 IP 即可高速访问！

---

### 3.3 方式 B：Docker 容器化部署（备选）

如果您更喜欢容器化一键交付，可以在项目根目录创建 `Dockerfile`：

#### 1. 项目根目录创建 `Dockerfile`：
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# 设置时区与防 Python 输出缓冲
ENV TZ=Asia/Shanghai \
    PYTHONUNBUFFERED=1

COPY backend/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

COPY . .

EXPOSE 8000

CMD ["uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
```

#### 2. 在宝塔 Docker 模块运行：
```bash
# 构建镜像
docker build -t file-desensitizer:latest .

# 启动容器（设置自动重启与端口映射）
docker run -d --name file-desensitize-app \
  -p 8000:8000 \
  --restart always \
  file-desensitizer:latest
```

---

## 四、 内网自动化运维与沙箱定时清理

虽然系统内置了 **“30分钟阅后即焚守护线程”**，为了给服务器磁盘双重保险，建议在宝塔面板配置一条每日计划任务：

1. 宝塔后台 $\rightarrow$ **【计划任务】**；
2. **任务类型**：Shell 脚本；
3. **任务名称**：`清理脱敏工具临时缓存`；
4. **执行周期**：每天凌晨 03:00 执行；
5. **脚本内容**：
```bash
# 自动清理 1 小时以前残留的临时上传与脱敏文件（安全双保险）
find /www/wwwroot/file-desensitization/backend/temp/uploads -type f -mmin +60 -delete
find /www/wwwroot/file-desensitization/backend/temp/processed -type f -mmin +60 -delete
echo "脱敏临时沙箱清理完成: $(date)"
```

---

## 五、 常见问题排查 (FAQ)

### Q1: 上传大文件（如超过 30MB）时页面提示“413 Request Entity Too Large”？
- **原因**：Nginx 默认限制单文件上传不能超过 50MB。
- **解决**：在宝塔 Nginx 站点配置中增加 `client_max_body_size 100m;`。

### Q2: 局域网其他同事电脑打不开网页？
- **排查步骤**：
  1. 检查启动命令是否绑定了 `0.0.0.0`（而不是 `127.0.0.1`）；
  2. 检查服务器/主机安全组及宝塔 **【安全】** 页面是否放行了对应端口（如 `8000`）；
  3. Linux 执行 `ufw allow 8000` 或 `firewall-cmd --add-port=8000/tcp --permanent`。

### Q3: 为什么不需要配置 MySQL 数据库？
- **设计原理**：为了践行真正的 **“零数据驻留 / 绝密安全”**，本系统采用纯内存流式排队与沙箱临时缓存设计，**完全不依赖外部数据库**，真正做到“零配置、轻量级、无泄漏风险”。

### Q4: 本地打开页面只显示 `{"detail":"Not Found"}`？
- **常见原因**：`127.0.0.1:8000` 被**其他项目的 uvicorn**（例如 `api.main:app`）或已退出仍残留的「幽灵监听」占用。本项目虽已在 `0.0.0.0:8000` 启动，但浏览器访问 localhost 会优先打到错误进程，于是只看到 FastAPI 默认 404 JSON。
- **快速确认**：
  1. 用局域网 IP 访问（如 `http://192.168.x.x:8000`）若正常，即可确认是本机 127.0.0.1 端口冲突；
  2. 访问 `http://127.0.0.1:8000/api/tasks`，若不是带 `tasks` 字段的 JSON，说明打错服务了。
- **处理办法**：
  1. PowerShell：`netstat -ano | findstr ":8000"`，对 LISTENING 的 PID 执行 `taskkill /PID <PID> /F` 后重新启动；
  2. 或换端口：`set AIMASK_PORT=8001` 再执行 `python run.py`；
  3. 推荐直接使用项目根目录的 `python run.py` / `启动工具站.bat`（已内置端口占用检测与自动换端口，请以控制台打印的地址为准）。
- **详细复盘**：见 [`.phrase/docs/ISSUES.md` → issue001](file:///e:/AIProject/File%20Desensitization/.phrase/docs/ISSUES.md)。
