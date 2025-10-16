document.addEventListener("DOMContentLoaded", function () {
    // Elements
    const backupBtn = document.getElementById("backupBtn");
    const restoreBtn = document.getElementById("restoreBtn");
    const restoreFile = document.getElementById("restoreFile");
    const backupName = document.getElementById("backupName");
    const backupHistoryTableBody = document.querySelector("#backupHistoryTableBody");
    const refreshBtn = document.getElementById("refreshBtn");
    const historyStatusText = document.getElementById("historyStatusText");
    
    // Security: Input sanitization
    function sanitizeInput(input) {
        if (typeof input !== 'string') {
            input = String(input);
        }
        const div = document.createElement('div');
        div.textContent = input;
        return div.innerHTML;
    }
    
    // Enhanced XSS protection
    function escapeHTML(str) {
        return str
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#39;');
    }
    
    // Security: Validate file type
    function validateFileType(file) {
        const allowedTypes = ['.json'];
        const extension = file.name.toLowerCase().substring(file.name.lastIndexOf('.'));
        return allowedTypes.includes(extension);
    }
    
    // Security: Validate file size (50MB max)
    function validateFileSize(file) {
        const maxSize = 50 * 1024 * 1024; // 50MB
        return file.size <= maxSize;
    }

    // Configuration
    const INITIAL_DISPLAY_LIMIT = 5;
    let allBackups = [];
    let displayLimit = INITIAL_DISPLAY_LIMIT;
    let isLoading = false;

    // CSRF token
    function getCookie(name) {
        const value = `; ${document.cookie}`;
        const parts = value.split(`; ${name}=`);
        if (parts.length === 2) return parts.pop().split(';').shift();
    }
    const csrftoken = getCookie('csrftoken');

    // Initialize
    loadBackupHistory();
    setupScrollLoading();

    // Display backup history with XSS protection
    function displayBackupHistory(backups, limit = null) {
        const displayBackups = limit ? backups.slice(0, limit) : backups;

        backupHistoryTableBody.innerHTML = displayBackups.length === 0
            ? `<tr><td colspan="4" class="text-center py-4 text-gray-500">No backups found</td></tr>`
            : displayBackups.map(item => `
                <tr class="hover:bg-gray-50">
                    <td class="p-3">${sanitizeInput(item.file_name)}</td>
                    <td class="p-3">${new Date(item.date).toLocaleString()}</td>
                    <td class="p-3">
                        <span class="px-2 py-1 rounded-full text-xs ${item.operation_type === 'backup'
                    ? 'bg-blue-100 text-blue-800'
                    : 'bg-green-100 text-green-800'}">
                            ${sanitizeInput(item.operation_type.charAt(0).toUpperCase() + item.operation_type.slice(1))}
                        </span>
                    </td>
                    <td class="p-3 flex space-x-2">
                        <button onclick="confirmRestore(${parseInt(item.id)}, '${sanitizeInput(item.file_name).replace(/'/g, "\\'")}')"
                            class="flex items-center bg-blue-600 text-white px-3 py-1 rounded hover:bg-blue-700 text-sm transition-colors">
                            <i class="fas fa-upload mr-1"></i> Restore
                        </button>
                        <button onclick="confirmDelete(${parseInt(item.id)}, '${sanitizeInput(item.file_name).replace(/'/g, "\\'")}')"
                            class="flex items-center bg-red-600 text-white px-3 py-1 rounded hover:bg-red-700 text-sm transition-colors">
                            <i class="fas fa-trash mr-1"></i> Delete
                        </button>
                    </td>
                </tr>
            `).join('');

        historyStatusText.textContent = limit
            ? `Showing latest ${Math.min(limit, backups.length)} of ${backups.length} backups`
            : `Showing all ${backups.length} backups`;
    }

    // Load backup history
    async function loadBackupHistory() {
        try {
            isLoading = true;
            backupHistoryTableBody.innerHTML = `
                <tr>
                    <td colspan="4" class="text-center py-4">
                        <div class="animate-pulse">Loading...</div>
                    </td>
                </tr>`;

            const response = await fetch("/backup/history/");
            if (!response.ok) throw new Error('Network response was not ok');

            const data = await response.json();
            if (data.status !== 'success') throw new Error(data.message);

            allBackups = data.data;
            displayBackupHistory(allBackups, displayLimit);
        } catch (error) {
            console.error("Error loading backup history:", error);
            backupHistoryTableBody.innerHTML = `
                <tr>
                    <td colspan="4" class="text-center py-4 text-red-500">
                        Failed to load backup history: ${error.message}
                    </td>
                </tr>`;
            showAlert(`Error loading backup history: ${error.message}`, 'error');
        } finally {
            isLoading = false;
        }
    }

    // Setup scroll loading
    function setupScrollLoading() {
        const tableContainer = document.querySelector('.overflow-y-auto');
        tableContainer.addEventListener('scroll', function () {
            if (isLoading) return;

            const { scrollTop, scrollHeight, clientHeight } = this;
            const isNearBottom = scrollTop + clientHeight >= scrollHeight - 50;

            if (isNearBottom && displayLimit < allBackups.length) {
                displayLimit += 5;
                displayBackupHistory(allBackups, displayLimit);
            }
        });
    }

    // Create backup with validation
    backupBtn.addEventListener("click", async function () {
        const backupNameValue = sanitizeInput(backupName.value.trim());
        let fileName = '';

        if (backupNameValue) {
            // Security: Strict filename validation
            fileName = backupNameValue.replace(/[^a-zA-Z0-9_-]/g, '');
            if (fileName.length > 50) {
                showAlert("Backup name must be less than 50 characters", 'error');
                return;
            }
            if (fileName.length === 0) {
                showAlert("Invalid backup name. Use only letters, numbers, hyphens and underscores.", 'error');
                return;
            }
        }

        try {
            backupBtn.disabled = true;
            backupBtn.innerHTML = '<i class="fas fa-spinner fa-spin mr-2"></i> Creating Backup...';

            const response = await fetch("/backup/create/", {
                method: "POST",
                headers: {
                    'X-CSRFToken': csrftoken,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ backup_name: fileName })
            });

            if (!response.ok) throw new Error('Network response was not ok');

            const data = await response.json();
            showAlert(data.message || 'Backup created successfully', 'success');
            backupName.value = '';
            await loadBackupHistory();
            displayLimit = INITIAL_DISPLAY_LIMIT; // Reset display limit
        } catch (error) {
            console.error("Backup error:", error);
            showAlert(`Backup failed: ${error.message}`, 'error');
        } finally {
            backupBtn.disabled = false;
            backupBtn.innerHTML = '<i class="fas fa-save mr-2"></i> Create Backup Now';
        }
    });

    // Restore backup with security validation
    restoreBtn.addEventListener("click", async function () {
        if (!restoreFile.files[0]) {
            showAlert("Please select a backup file.", 'error');
            return;
        }
        
        // Security: Validate file type and size
        const file = restoreFile.files[0];
        if (!validateFileType(file)) {
            showAlert("Only JSON files are allowed.", 'error');
            return;
        }
        
        if (!validateFileSize(file)) {
            showAlert("File size exceeds 50MB limit.", 'error');
            return;
        }

        if (!confirm("WARNING: This will overwrite your current database. Continue?")) {
            return;
        }

        try {
            restoreBtn.disabled = true;
            restoreBtn.innerHTML = '<i class="fas fa-spinner fa-spin mr-2"></i> Restoring...';

            const formData = new FormData();
            formData.append("backup_file", restoreFile.files[0]);

            const response = await fetch("/backup/restore/", {
                method: "POST",
                headers: { 'X-CSRFToken': csrftoken },
                body: formData
            });

            if (!response.ok) throw new Error('Network response was not ok');

            const data = await response.json();
            showAlert(data.message || 'Database restored successfully', 'success');
            restoreFile.value = "";
            await loadBackupHistory();
        } catch (error) {
            console.error("Restore error:", error);
            showAlert(`Restore failed: ${error.message}`, 'error');
        } finally {
            restoreBtn.disabled = false;
            restoreBtn.innerHTML = '<i class="fas fa-upload mr-2"></i> Restore Backup';
        }
    });

    // Refresh button
    refreshBtn.addEventListener("click", function () {
        refreshBtn.innerHTML = '<i class="fas fa-spinner fa-spin mr-1"></i> Refreshing';
        loadBackupHistory().then(() => {
            displayLimit = INITIAL_DISPLAY_LIMIT;
            refreshBtn.innerHTML = '<i class="fas fa-sync-alt mr-1"></i> Refresh';
        });
    });

    // Global functions for table buttons
    window.confirmRestore = function (backupId, fileName) {
        if (confirm(`Restore from ${fileName}? This will overwrite your current database.`)) {
            restoreFromHistory(backupId);
        }
    };

    window.confirmDelete = function (backupId, fileName) {
        if (confirm(`Permanently delete backup: ${fileName}?`)) {
            deleteBackup(backupId);
        }
    };

    // Restore from history
    async function restoreFromHistory(backupId) {
        try {
            const response = await fetch(`/backup/restore-from-history/${backupId}/`, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': csrftoken,
                    'Content-Type': 'application/json'
                }
            });

            if (!response.ok) throw new Error('Network response was not ok');

            const data = await response.json();
            if (data.status !== 'success') throw new Error(data.message);

            showAlert('Database restored successfully!', 'success');
            await loadBackupHistory();
        } catch (error) {
            console.error('Restore error:', error);
            showAlert(`Error: ${error.message}`, 'error');
        }
    }

    // Delete backup
    async function deleteBackup(backupId) {
        try {
            const response = await fetch(`/backup/delete/${backupId}/`, {
                method: 'DELETE',
                headers: {
                    'X-CSRFToken': csrftoken,
                    'Content-Type': 'application/json'
                }
            });

            if (!response.ok) throw new Error('Network response was not ok');

            const data = await response.json();
            if (data.status !== 'success') throw new Error(data.message);

            showAlert('Backup deleted successfully!', 'success');
            await loadBackupHistory();
            displayLimit = INITIAL_DISPLAY_LIMIT; // Reset display limit
        } catch (error) {
            console.error('Delete error:', error);
            showAlert(`Error: ${error.message}`, 'error');
        }
    }

    // Show alert message
    function showAlert(message, type) {
        const toast = document.getElementById('toastMessage');

        toast.textContent = message;
        toast.className = `fixed top-5 right-5 z-50 p-4 rounded-xl shadow-lg text-sm font-medium transition-all duration-300 
        ${type === 'success' ? 'bg-green-600' : 'bg-red-600'} text-white`;

        toast.classList.remove('hidden');
        toast.style.opacity = '1';

        setTimeout(() => {
            toast.style.opacity = '0';
            setTimeout(() => toast.classList.add('hidden'), 300);  // delay before hiding again
        }, 3000);
    }

});