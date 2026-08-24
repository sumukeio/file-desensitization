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

    // Diff 模态框元素
    const diffModal = document.getElementById('diffModal');
    const closeModalBtn = document.getElementById('closeModalBtn');
    const modalCloseActionBtn = document.getElementById('modalCloseActionBtn');
    const modalFileName = document.getElementById('modalFileName');
    const modalMaskedCount = document.getElementById('modalMaskedCount');
    const diffTableBody = document.getElementById('diffTableBody');

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

            tr.innerHTML = `
                <td><strong>${escapeHtml(task.file_name)}</strong></td>
                <td>${formatBytes(task.file_size)}</td>
                <td><span style="font-size:12px; color:var(--text-secondary);">${profileLabel}</span></td>
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

    // 5. Diff 模态框展示
    async function openDiffModal(taskId) {
        try {
            const resp = await fetch(`/api/tasks/${taskId}/diff`);
            if (!resp.ok) {
                alert('获取 Diff 失败');
                return;
            }
            const data = await resp.json();
            modalFileName.textContent = `脱敏效果对比 — ${data.file_name}`;
            modalMaskedCount.textContent = data.masked_count;

            diffTableBody.innerHTML = '';
            const samples = data.diff_samples || [];

            if (samples.length === 0) {
                diffTableBody.innerHTML = `<tr><td colspan="6" style="text-align:center; padding:20px; color:#94a3b8;">该文件未检测到需要修改的敏感内容</td></tr>`;
            } else {
                samples.forEach(s => {
                    const row = document.createElement('tr');
                    row.innerHTML = `
                        <td>${escapeHtml(s.sheet || 'Sheet1')}</td>
                        <td><code>R${s.row}C${s.col}</code></td>
                        <td><strong>${escapeHtml(s.col_name || '')}</strong></td>
                        <td><span class="status-pill status-processing">${escapeHtml(s.mask_type || 'MASK')}</span></td>
                        <td><span class="diff-raw">${escapeHtml(s.original || '')}</span></td>
                        <td><span class="diff-masked">${escapeHtml(s.desensitized || '')}</span></td>
                    `;
                    diffTableBody.appendChild(row);
                });
            }

            diffModal.classList.add('show');
        } catch (err) {
            console.error('打开 Diff 弹窗失败:', err);
        }
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

    // 7. 打包下载与清空
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

    // 页面载入初始拉取一次
    fetchTasks();
});
