// AI-Mask 前端主应用交互逻辑
document.addEventListener('DOMContentLoaded', () => {
    // 状态与 DOM 元素
    let currentProfile = 'ai_friendly';
    let pollInterval = null;
    let isPolling = false;

    const profileCards = document.querySelectorAll('.profile-card');
    const dropzone = document.getElementById('dropzone');
    const fileInput = document.getElementById('fileInput');
    const selectFilesBtn = document.getElementById('selectFilesBtn');
    const taskTableBody = document.getElementById('taskTableBody');
    const emptyQueueRow = document.getElementById('emptyQueueRow');
    const queueStatsSummary = document.getElementById('queueStatsSummary');
    const downloadAllBtn = document.getElementById('downloadAllBtn');
    const clearCompletedBtn = document.getElementById('clearCompletedBtn');
    const maskHeadersCheckbox = document.getElementById('maskHeaders');
    const maskSheetNamesCheckbox = document.getElementById('maskSheetNames');
    const headerRowModeAuto = document.getElementById('headerRowModeAuto');
    const headerRowModeManual = document.getElementById('headerRowModeManual');
    const headerRowInput = document.getElementById('headerRowInput');

    // Diff 模态框元素
    const diffModal = document.getElementById('diffModal');
    const closeModalBtn = document.getElementById('closeModalBtn');
    const modalCloseActionBtn = document.getElementById('modalCloseActionBtn');
    const modalFileName = document.getElementById('modalFileName');
    const modalMaskedCount = document.getElementById('modalMaskedCount');
    const sheetRenamesSummary = document.getElementById('sheetRenamesSummary');
    const diffSheetTabs = document.getElementById('diffSheetTabs');
    const diffSheetMeta = document.getElementById('diffSheetMeta');
    const diffStructureSection = document.getElementById('diffStructureSection');
    const diffStructureBody = document.getElementById('diffStructureBody');
    const diffDataSection = document.getElementById('diffDataSection');
    const diffDataBody = document.getElementById('diffDataBody');
    let currentDiffPayload = null;
    let currentDiffTaskId = null;
    let activeDiffSheet = null;

    // 表头位置：自动 / 手动
    function syncHeaderRowInputState() {
        if (!headerRowInput || !headerRowModeManual) return;
        headerRowInput.disabled = !headerRowModeManual.checked;
    }
    if (headerRowModeAuto && headerRowModeManual) {
        headerRowModeAuto.addEventListener('change', syncHeaderRowInputState);
        headerRowModeManual.addEventListener('change', syncHeaderRowInputState);
        syncHeaderRowInputState();
    }

    // 1. 策略选择卡片交互
    profileCards.forEach(card => {
        card.addEventListener('click', () => {
            profileCards.forEach(c => c.classList.remove('active'));
            card.classList.add('active');
            const radio = card.querySelector('input[type="radio"]');
            if (radio) {
                radio.checked = true;
                currentProfile = radio.value;
            }
        });
    });

    // 2. 拖拽上传与文件选择
    selectFilesBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        fileInput.click();
    });

    dropzone.addEventListener('click', () => {
        fileInput.click();
    });

    ['dragenter', 'dragover'].forEach(eventName => {
        dropzone.addEventListener(eventName, (e) => {
            e.preventDefault();
            e.stopPropagation();
            dropzone.classList.add('dragover');
        });
    });

    ['dragleave', 'drop'].forEach(eventName => {
        dropzone.addEventListener(eventName, (e) => {
            e.preventDefault();
            e.stopPropagation();
            dropzone.classList.remove('dragover');
        });
    });

    dropzone.addEventListener('drop', (e) => {
        const dt = e.dataTransfer;
        const files = dt.files;
        if (files && files.length > 0) {
            handleFileUpload(files);
        }
    });

    fileInput.addEventListener('change', (e) => {
        if (fileInput.files && fileInput.files.length > 0) {
            handleFileUpload(fileInput.files);
            fileInput.value = ''; // 重置以支持重复选同名文件
        }
    });

    // 3. 上传文件到后端 API
    async function handleFileUpload(files) {
        const formData = new FormData();
        formData.append('profile', currentProfile);
        formData.append('mask_headers', maskHeadersCheckbox && maskHeadersCheckbox.checked ? 'true' : 'false');
        formData.append('mask_sheet_names', maskSheetNamesCheckbox && maskSheetNamesCheckbox.checked ? 'true' : 'false');
        const headerMode = headerRowModeManual && headerRowModeManual.checked ? 'manual' : 'auto';
        formData.append('header_row_mode', headerMode);
        if (headerMode === 'manual' && headerRowInput) {
            formData.append('header_row', String(headerRowInput.value || '1'));
        }
        let validFileCount = 0;

        for (let i = 0; i < files.length; i++) {
            const f = files[i];
            const lowerName = f.name.toLowerCase();
            if (lowerName.endsWith('.xlsx') || lowerName.endsWith('.xls') || lowerName.endsWith('.csv')) {
                formData.append('files', f);
                validFileCount++;
            }
        }

        if (validFileCount === 0) {
            alert('请上传有效的 Excel 或 CSV 文件 (.xlsx, .xls, .csv)');
            return;
        }

        try {
            const resp = await fetch('/api/upload', {
                method: 'POST',
                body: formData
            });

            if (!resp.ok) {
                const err = await resp.json();
                alert('上传失败: ' + (err.detail || resp.statusText));
                return;
            }

            // 触发立即拉取并启动高频轮询
            await fetchTasks();
            startPolling();
        } catch (err) {
            console.error('上传出错:', err);
            alert('网络异常或服务器未连接，请确认后台服务已启动');
        }
    }

    // 4. 轮询拉取任务状态
    async function fetchTasks() {
        try {
            const resp = await fetch('/api/tasks');
            if (!resp.ok) return;
            const data = await resp.json();
            renderTasks(data.tasks || []);
        } catch (err) {
            console.warn('获取任务列表失败:', err);
        }
    }

    function renderTasks(tasks) {
        if (!tasks || tasks.length === 0) {
            taskTableBody.innerHTML = '';
            taskTableBody.appendChild(emptyQueueRow);
            queueStatsSummary.textContent = '当前队列：0 个文件';
            downloadAllBtn.disabled = true;
            return;
        }

        taskTableBody.innerHTML = '';
        let completedCount = 0;
        let hasActiveTasks = false;

        tasks.forEach(task => {
            if (task.status === 'completed') completedCount++;
            if (task.status === 'pending' || task.status === 'processing') hasActiveTasks = true;

            const tr = document.createElement('tr');

            // 策略名称格式化 (大白话)
            let profileLabel = '🌟 智能 AI 模式';
            if (task.profile === 'standard_mask') profileLabel = '🛡️ 经典打星模式';
            if (task.profile === 'strict_anon') profileLabel = '🔒 绝密粉碎模式';

            // 状态徽章
            let statusBadge = `<span class="status-pill status-pending">⏳ 排队中</span>`;
            if (task.status === 'processing') statusBadge = `<span class="status-pill status-processing">⚡ 脱敏中</span>`;
            if (task.status === 'completed') statusBadge = `<span class="status-pill status-completed">✅ 已完成</span>`;
            if (task.status === 'failed') statusBadge = `<span class="status-pill status-failed">❌ 失败</span>`;

            // 进度条
            const isFinished = task.status === 'completed';
            const progressHtml = `
                <div class="progress-bar-container">
                    <div class="progress-bar-fill ${isFinished ? 'success' : ''}" style="width: ${task.progress}%;"></div>
                </div>
                <span>${task.progress}%</span>
            `;

            // 操作按钮
            let actionsHtml = `<span class="text-muted" style="color:#94a3b8;">处理中...</span>`;
            if (task.status === 'completed') {
                actionsHtml = `
                    <div class="cell-actions">
                        <button class="btn btn-outline btn-sm view-diff-btn" data-id="${task.task_id}">👁️ 效果对比</button>
                        <a class="btn btn-primary btn-sm" href="/api/tasks/${task.task_id}/download" download>⬇️ 下载</a>
                    </div>
                `;
            } else if (task.status === 'failed') {
                actionsHtml = `<span style="color:var(--danger); font-size:12px;" title="${task.error_message || '未知错误'}">处理失败</span>`;
            }

            const structureTag = formatStructureOptions(task);
            const headerHint = formatHeaderRowsHint(task);

            tr.innerHTML = `
                <td>
                    <strong>${escapeHtml(task.file_name)}</strong>
                    ${headerHint}
                </td>
                <td>${formatBytes(task.file_size)}</td>
                <td>
                    <span style="font-size:12px; color:var(--text-secondary);">${profileLabel}</span>
                    ${structureTag}
                </td>
                <td>${statusBadge}</td>
                <td>${progressHtml}</td>
                <td><strong>${task.masked_count}</strong> 处</td>
                <td>${actionsHtml}</td>
            `;

            taskTableBody.appendChild(tr);
        });

        // 更新汇总摘要
        queueStatsSummary.textContent = `共 ${tasks.length} 个文件 | ${completedCount} 个已完成`;
        downloadAllBtn.disabled = completedCount === 0;

        // 绑定 Diff 预览按钮点击事件
        document.querySelectorAll('.view-diff-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                const taskId = btn.getAttribute('data-id');
                openDiffModal(taskId);
            });
        });

        // 若已无活动任务，降低轮询频率或暂停
        if (!hasActiveTasks && isPolling) {
            stopPolling();
        }
    }

    function startPolling() {
        if (isPolling) return;
        isPolling = true;
        pollInterval = setInterval(fetchTasks, 1000);
    }

    function stopPolling() {
        if (pollInterval) {
            clearInterval(pollInterval);
            pollInterval = null;
        }
        isPolling = false;
    }

    // 5. Diff 模态框展示（分 Sheet Tab + 结构脱敏可见）
    async function openDiffModal(taskId) {
        try {
            const resp = await fetch(`/api/tasks/${taskId}/diff`);
            if (!resp.ok) {
                alert('获取 Diff 失败');
                return;
            }
            const data = await resp.json();
            currentDiffPayload = data;
            currentDiffTaskId = data.task_id || taskId;
            modalFileName.textContent = `脱敏效果对比 — ${data.file_name}`;
            modalMaskedCount.textContent = data.masked_count;
            renderSheetRenamesSummary(data);
            renderDiffSheetTabs(data);
            diffModal.classList.add('show');
        } catch (err) {
            console.error('打开 Diff 弹窗失败:', err);
        }
    }

    function getDiffSheetList(data) {
        const names = new Set(Object.keys(data.header_rows || {}));
        (data.diff_samples || []).forEach(s => {
            if (s.sheet) names.add(s.sheet);
        });
        return Array.from(names);
    }

    function renderSheetRenamesSummary(data) {
        if (!sheetRenamesSummary) return;
        const renames = data.sheet_renames || {};
        const count = Object.keys(renames).length;
        if (count === 0) {
            sheetRenamesSummary.classList.remove('show');
            sheetRenamesSummary.innerHTML = '';
            return;
        }
        sheetRenamesSummary.innerHTML = `已将 <strong>${count}</strong> 个工作表重命名（切换上方标签可看「原名 → 新名」）`;
        sheetRenamesSummary.classList.add('show');
    }

    function renderDiffSheetTabs(data) {
        if (!diffSheetTabs) return;
        const sheets = getDiffSheetList(data);
        diffSheetTabs.innerHTML = '';
        if (sheets.length === 0) {
            renderDiffSheetPanel(data, null);
            return;
        }
        sheets.forEach((sheetName, idx) => {
            const btn = document.createElement('button');
            btn.type = 'button';
            btn.className = 'diff-sheet-tab' + (idx === 0 ? ' active' : '');
            const renamed = (data.sheet_renames || {})[sheetName];
            btn.innerHTML = renamed
                ? `${escapeHtml(sheetName)} <span class="tab-sub">→ ${escapeHtml(renamed)}</span>`
                : escapeHtml(sheetName);
            btn.title = renamed ? `${sheetName} → ${renamed}` : sheetName;
            btn.addEventListener('click', () => {
                document.querySelectorAll('.diff-sheet-tab').forEach(el => el.classList.remove('active'));
                btn.classList.add('active');
                renderDiffSheetPanel(data, sheetName);
                btn.scrollIntoView({ inline: 'nearest', block: 'nearest', behavior: 'smooth' });
            });
            diffSheetTabs.appendChild(btn);
        });
        renderDiffSheetPanel(data, sheets[0]);
    }

    function renderDiffSheetPanel(data, sheetName) {
        activeDiffSheet = sheetName;
        if (!diffSheetMeta || !diffStructureBody || !diffDataBody) return;

        if (!sheetName) {
            diffSheetMeta.textContent = '未识别到可展示的工作表。';
            diffStructureBody.innerHTML = '';
            diffDataBody.innerHTML = '';
            return;
        }

        const headerRow = (data.header_rows || {})[sheetName];
        const overrides = data.header_row_overrides || {};
        const isOverridden = Object.prototype.hasOwnProperty.call(overrides, sheetName);
        let modeText = '自动识别';
        if (isOverridden) {
            modeText = '本工作表已手动纠错';
        } else if (data.header_row_mode === 'manual') {
            modeText = `手动指定（统一第 ${data.header_row || '?'} 行）`;
        }

        const defaultInput = isOverridden ? overrides[sheetName] : (headerRow || 1);
        diffSheetMeta.innerHTML = `
            <div class="diff-sheet-meta-line">
                ${headerRow
                    ? `本工作表表头识别为<strong>第 ${headerRow} 行</strong>（${modeText}）`
                    : `本工作表：${escapeHtml(sheetName)}`}
            </div>
            <div class="header-override-bar">
                <label>若识别不准，仅改本工作表为第
                    <input type="number" class="header-override-input" id="headerOverrideInput" min="1" max="100" value="${defaultInput}">
                    行
                </label>
                <button type="button" class="btn btn-secondary btn-sm" id="headerOverrideBtn">按此行重跑</button>
                ${isOverridden ? '<button type="button" class="btn btn-ghost btn-sm" id="headerOverrideClearBtn">恢复自动识别</button>' : ''}
            </div>
            <div class="header-override-hint">其它工作表不受影响；将复用原文件重新脱敏。</div>
        `;

        const overrideBtn = document.getElementById('headerOverrideBtn');
        const clearBtn = document.getElementById('headerOverrideClearBtn');
        const overrideInput = document.getElementById('headerOverrideInput');
        if (overrideBtn && overrideInput) {
            overrideBtn.addEventListener('click', () => {
                submitHeaderOverride(sheetName, overrideInput.value, false);
            });
        }
        if (clearBtn) {
            clearBtn.addEventListener('click', () => {
                submitHeaderOverride(sheetName, '', true);
            });
        }

        const samples = (data.diff_samples || []).filter(s => s.sheet === sheetName);
        const structureSamples = samples.filter(s => s.mask_type === 'HEADER' || s.mask_type === 'SHEET');
        const dataSamples = samples.filter(s => s.mask_type !== 'HEADER' && s.mask_type !== 'SHEET');

        if (structureSamples.length === 0) {
            diffStructureSection.style.display = 'none';
            diffStructureBody.innerHTML = '';
        } else {
            diffStructureSection.style.display = 'block';
            diffStructureBody.innerHTML = structureSamples.map(s => {
                const pos = s.mask_type === 'SHEET'
                    ? '工作表名称'
                    : `<code>R${s.row}C${s.col}</code>`;
                return `
                    <tr>
                        <td>${pos}</td>
                        <td><span class="status-pill status-processing">${escapeHtml(formatMaskTypeLabel(s.mask_type))}</span></td>
                        <td><span class="diff-raw">${escapeHtml(s.original || '')}</span></td>
                        <td><span class="diff-masked">${escapeHtml(s.desensitized || '')}</span></td>
                    </tr>
                `;
            }).join('');
        }

        if (dataSamples.length === 0) {
            diffDataBody.innerHTML = `<tr><td colspan="5" style="text-align:center;padding:16px;color:#94a3b8;">本工作表暂无数据单元格变更样本</td></tr>`;
        } else {
            diffDataBody.innerHTML = dataSamples.map(s => `
                <tr>
                    <td><code>R${s.row}C${s.col}</code></td>
                    <td><strong>${escapeHtml(s.col_name || '')}</strong></td>
                    <td><span class="status-pill status-processing">${escapeHtml(formatMaskTypeLabel(s.mask_type))}</span></td>
                    <td><span class="diff-raw">${escapeHtml(s.original || '')}</span></td>
                    <td><span class="diff-masked">${escapeHtml(s.desensitized || '')}</span></td>
                </tr>
            `).join('');
        }
    }

    async function submitHeaderOverride(sheetName, headerRowValue, clearOverride) {
        if (!currentDiffTaskId) return;
        const formData = new FormData();
        formData.append('sheet_name', sheetName);
        formData.append('clear_override', clearOverride ? 'true' : 'false');
        if (!clearOverride) {
            formData.append('header_row', String(headerRowValue || '1'));
        }
        try {
            const resp = await fetch(`/api/tasks/${currentDiffTaskId}/reprocess`, {
                method: 'POST',
                body: formData,
            });
            if (!resp.ok) {
                const err = await resp.json().catch(() => ({}));
                alert(err.detail || '纠错重跑失败');
                return;
            }
            diffModal.classList.remove('show');
            await fetchTasks();
            await waitAndReopenDiff(currentDiffTaskId, sheetName);
        } catch (err) {
            console.error('纠错重跑失败:', err);
            alert('纠错重跑失败，请稍后重试');
        }
    }

    async function waitAndReopenDiff(taskId, preferredSheet) {
        const maxTries = 40;
        for (let i = 0; i < maxTries; i++) {
            try {
                const resp = await fetch('/api/tasks');
                const data = await resp.json();
                const task = (data.tasks || []).find(t => t.task_id === taskId);
                if (task && task.status === 'completed') {
                    await openDiffModal(taskId);
                    if (preferredSheet && currentDiffPayload) {
                        renderDiffSheetPanel(currentDiffPayload, preferredSheet);
                        const sheets = getDiffSheetList(currentDiffPayload);
                        document.querySelectorAll('.diff-sheet-tab').forEach((btn, idx) => {
                            btn.classList.toggle('active', sheets[idx] === preferredSheet);
                        });
                    }
                    return;
                }
                if (task && task.status === 'failed') {
                    alert(task.error_message || '重跑失败');
                    return;
                }
            } catch (e) {
                console.error(e);
            }
            await new Promise(r => setTimeout(r, 500));
        }
        alert('重跑仍在进行中，请稍后在任务列表中查看并打开效果对比。');
    }

    function closeDiffModal() {
        diffModal.classList.remove('show');
    }

    closeModalBtn.addEventListener('click', closeDiffModal);
    modalCloseActionBtn.addEventListener('click', closeDiffModal);
    diffModal.addEventListener('click', (e) => {
        if (e.target === diffModal) closeDiffModal();
    });

    // 6. 安全政策 QA 模态框交互
    const securityBadge = document.getElementById('securityBadge');
    const securityModal = document.getElementById('securityModal');
    const closeSecurityModalBtn = document.getElementById('closeSecurityModalBtn');
    const securityModalConfirmBtn = document.getElementById('securityModalConfirmBtn');

    function openSecurityModal() {
        securityModal.classList.add('show');
    }

    function closeSecurityModal() {
        securityModal.classList.remove('show');
    }

    if (securityBadge && securityModal) {
        securityBadge.addEventListener('click', openSecurityModal);
        closeSecurityModalBtn.addEventListener('click', closeSecurityModal);
        securityModalConfirmBtn.addEventListener('click', closeSecurityModal);
        securityModal.addEventListener('click', (e) => {
            if (e.target === securityModal) closeSecurityModal();
        });
    }

    // 7. 最近更新（方案 A+B）
    const whatsNewBadge = document.getElementById('whatsNewBadge');
    const whatsNewUnreadDot = document.getElementById('whatsNewUnreadDot');
    const whatsNewModal = document.getElementById('whatsNewModal');
    const whatsNewTimeline = document.getElementById('whatsNewTimeline');
    const closeWhatsNewModalBtn = document.getElementById('closeWhatsNewModalBtn');
    const whatsNewConfirmBtn = document.getElementById('whatsNewConfirmBtn');
    const whatsNewConfig = window.WHATS_NEW || { currentVersion: '0', storageKey: 'aimask_whats_new_read_version', releases: [] };

    function compareVersion(a, b) {
        if (!a) return -1;
        if (!b) return 1;
        return String(a).localeCompare(String(b));
    }

    function getReadVersion() {
        try {
            return localStorage.getItem(whatsNewConfig.storageKey) || '';
        } catch (err) {
            return '';
        }
    }

    function isWhatsNewUnread() {
        return compareVersion(getReadVersion(), whatsNewConfig.currentVersion) < 0;
    }

    function markWhatsNewAsRead() {
        try {
            localStorage.setItem(whatsNewConfig.storageKey, whatsNewConfig.currentVersion);
        } catch (err) {
            console.warn('无法写入已读版本:', err);
        }
        updateWhatsNewUnreadBadge();
    }

    function updateWhatsNewUnreadBadge() {
        if (!whatsNewUnreadDot) return;
        whatsNewUnreadDot.classList.toggle('show', isWhatsNewUnread());
    }

    function renderWhatsNewTimeline() {
        if (!whatsNewTimeline) return;
        const releases = whatsNewConfig.releases || [];
        if (releases.length === 0) {
            whatsNewTimeline.innerHTML = '<p style="color:#94a3b8;text-align:center;">暂无更新记录</p>';
            return;
        }
        whatsNewTimeline.innerHTML = releases.map((release, index) => {
            const isLatest = index === 0;
            const itemsHtml = (release.items || [])
                .map(item => `<li>${escapeHtml(item)}</li>`)
                .join('');
            return `
                <article class="whats-new-release ${isLatest ? 'is-latest' : ''}">
                    <div class="whats-new-release-header">
                        <h4>
                            ${escapeHtml(release.title || '更新')}
                            ${isLatest ? '<span class="whats-new-tag">最新</span>' : ''}
                        </h4>
                        <span class="whats-new-date">${escapeHtml(release.date || release.version || '')}</span>
                    </div>
                    <ul class="whats-new-list">${itemsHtml}</ul>
                </article>
            `;
        }).join('');
    }

    function openWhatsNewModal() {
        renderWhatsNewTimeline();
        whatsNewModal.classList.add('show');
    }

    function closeWhatsNewModal() {
        whatsNewModal.classList.remove('show');
    }

    if (whatsNewBadge && whatsNewModal) {
        whatsNewBadge.addEventListener('click', openWhatsNewModal);
        closeWhatsNewModalBtn.addEventListener('click', closeWhatsNewModal);
        whatsNewConfirmBtn.addEventListener('click', () => {
            markWhatsNewAsRead();
            closeWhatsNewModal();
        });
        whatsNewModal.addEventListener('click', (e) => {
            if (e.target === whatsNewModal) closeWhatsNewModal();
        });

        updateWhatsNewUnreadBadge();
        if (isWhatsNewUnread()) {
            setTimeout(openWhatsNewModal, 600);
        }
    }

    // 8. 打包下载与清空
    downloadAllBtn.addEventListener('click', () => {
        window.location.href = '/api/download-all';
    });

    clearCompletedBtn.addEventListener('click', async () => {
        try {
            await fetch('/api/tasks/clear', { method: 'POST' });
            await fetchTasks();
        } catch (err) {
            console.error('清理任务失败:', err);
        }
    });

    // 工具函数
    function formatBytes(bytes, decimals = 1) {
        if (!bytes || bytes === 0) return '0 B';
        const k = 1024;
        const dm = decimals < 0 ? 0 : decimals;
        const sizes = ['B', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i];
    }

    function escapeHtml(text) {
        if (!text) return '';
        const map = { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#039;' };
        return String(text).replace(/[&<>"']/g, m => map[m]);
    }

    function formatStructureOptions(task) {
        const parts = [];
        if (task.mask_headers) parts.push('列名');
        if (task.mask_sheet_names) parts.push('Sheet');
        if (parts.length === 0) return '';
        return `<span class="structure-tag" title="本次额外脱敏了：${parts.join('、')}">+ ${parts.join(' + ')}</span>`;
    }

    function formatHeaderRowsHint(task) {
        if (task.status !== 'completed') return '';
        const rows = task.header_rows || {};
        const entries = Object.entries(rows);
        if (entries.length === 0) return '';
        if (entries.length === 1) {
            const [sheet, row] = entries[0];
            return `<div class="header-row-hint" title="系统识别到的表头位置">表头：${escapeHtml(sheet)} → 第 ${row} 行</div>`;
        }
        const preview = entries.slice(0, 2)
            .map(([sheet, row]) => `${escapeHtml(sheet)}→第${row}行`)
            .join('；');
        const more = entries.length > 2 ? ` 等 ${entries.length} 个工作表` : '';
        return `<div class="header-row-hint" title="点击「效果对比」可查看全部工作表">表头识别：${preview}${more}</div>`;
    }

    function formatMaskTypeLabel(maskType) {
        const labels = {
            HEADER: '列名脱敏',
            SHEET: '工作表名称脱敏',
            NUMBER_KEEP: '数值保留',
            CATEGORY_KEEP: '分类保留',
            TEXT_MIDDLE_MASK: '中间打星',
            STRICT_ANON: '完全匿名',
        };
        if (!maskType) return '脱敏';
        if (labels[maskType]) return labels[maskType];
        if (maskType.startsWith('PII_')) return '隐私信息';
        if (maskType.startsWith('PSEUDO_')) return '假名替换';
        return maskType;
    }

    // 页面载入初始拉取一次
    fetchTasks();
});
