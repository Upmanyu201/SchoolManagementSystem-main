// Modern Backup Manager - 2025 Standards
class BackupManager {
    constructor() {
        this.apiEndpoints = {
            create: '/backup/api/create/',
            restore: '/backup/api/restore/upload/',
            restoreHistory: '/backup/api/restore/history/',
            history: '/backup/api/history/',
            status: '/backup/api/status/',
            download: '/backup/api/download/'
        };
        
        this.currentPage = 1;
        this.itemsPerPage = 10;
        this.totalItems = 0;
        this.isLoading = false;
        this.pollInterval = null;
        
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.loadBackupHistory();
        this.loadStatistics();
        this.loadRecentActivity();
        this.setupDragAndDrop();
        this.startPeriodicRefresh();
    }

    setupEventListeners() {
        // Modal controls
        document.getElementById('createBackupBtn')?.addEventListener('click', () => {
            this.showModal('createBackupModal');
        });

        document.getElementById('restoreUploadBtn')?.addEventListener('click', () => {
            this.showModal('restoreUploadModal');
        });

        // Close modals on outside click
        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('modal')) {
                this.hideModal(e.target.id);
            }
        });

        // Escape key to close modals
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                const openModal = document.querySelector('.modal.show');
                if (openModal) {
                    this.hideModal(openModal.id);
                }
            }
        });

        // File input change handler
        const fileInput = document.getElementById('backupFileInput');
        if (fileInput) {
            fileInput.addEventListener('change', this.handleFileSelect.bind(this));
        }

        // Pagination controls
        document.getElementById('prevPage')?.addEventListener('click', () => {
            if (this.currentPage > 1) {
                this.currentPage--;
                this.loadBackupHistory();
            }
        });

        document.getElementById('nextPage')?.addEventListener('click', () => {
            const maxPage = Math.ceil(this.totalItems / this.itemsPerPage);
            if (this.currentPage < maxPage) {
                this.currentPage++;
                this.loadBackupHistory();
            }
        });
    }

    setupDragAndDrop() {
        const fileInput = document.getElementById('backupFileInput');
        const dropZone = fileInput?.parentElement;

        if (!dropZone) return;

        ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
            dropZone.addEventListener(eventName, this.preventDefaults, false);
        });

        ['dragenter', 'dragover'].forEach(eventName => {
            dropZone.addEventListener(eventName, () => {
                dropZone.classList.add('border-blue-500', 'bg-blue-100');
            }, false);
        });

        ['dragleave', 'drop'].forEach(eventName => {
            dropZone.addEventListener(eventName, () => {
                dropZone.classList.remove('border-blue-500', 'bg-blue-100');
            }, false);
        });

        dropZone.addEventListener('drop', (e) => {
            const files = e.dataTransfer.files;
            if (files.length > 0) {
                fileInput.files = files;
                this.handleFileSelect({ target: fileInput });
            }
        }, false);
    }

    preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }

    handleFileSelect(e) {
        const file = e.target.files[0];
        const fileInfo = document.getElementById('fileInfo');
        
        if (!file || !fileInfo) return;

        // Validate file
        if (!file.name.endsWith('.json')) {
            this.showNotification('Please select a JSON backup file', 'error');
            e.target.value = '';
            fileInfo.classList.add('hidden');
            return;
        }

        if (file.size > 100 * 1024 * 1024) { // 100MB limit
            this.showNotification('File size exceeds 100MB limit', 'error');
            e.target.value = '';
            fileInfo.classList.add('hidden');
            return;
        }

        // Display file info
        const sizeInMB = (file.size / (1024 * 1024)).toFixed(2);
        const lastModified = new Date(file.lastModified).toLocaleString();
        
        fileInfo.innerHTML = `
            <div class="flex items-center space-x-4">
                <div class="w-12 h-12 bg-gradient-to-r from-blue-500 to-indigo-600 rounded-lg flex items-center justify-center">
                    <i class="fas fa-file-alt text-white text-xl"></i>
                </div>
                <div class="flex-1">
                    <p class="font-semibold text-gray-800">${file.name}</p>
                    <p class="text-sm text-gray-600">
                        Size: ${sizeInMB} MB • Modified: ${lastModified}
                    </p>
                    <div class="mt-2">
                        <div class="w-full bg-gray-200 rounded-full h-2">
                            <div class="bg-gradient-to-r from-blue-500 to-indigo-600 h-2 rounded-full animate-pulse" style="width: 100%"></div>
                        </div>
                    </div>
                </div>
                <div class="text-green-500">
                    <i class="fas fa-check-circle text-2xl"></i>
                </div>
            </div>
        `;
        fileInfo.classList.remove('hidden');
    }

    showModal(modalId) {
        const modal = document.getElementById(modalId);
        if (modal) {
            modal.classList.add('show');
            document.body.style.overflow = 'hidden';
            
            // Focus first input
            const firstInput = modal.querySelector('input, select, textarea');
            if (firstInput) {
                setTimeout(() => firstInput.focus(), 100);
            }
        }
    }

    hideModal(modalId) {
        const modal = document.getElementById(modalId);
        if (modal) {
            modal.classList.remove('show');
            document.body.style.overflow = 'auto';
            
            // Reset form
            const form = modal.querySelector('form');
            if (form) {
                form.reset();
                const fileInfo = modal.querySelector('#fileInfo');
                if (fileInfo) {
                    fileInfo.classList.add('hidden');
                }
            }
        }
    }

    showProgress(title, message, percent = 0) {
        const indicator = document.getElementById('progressIndicator');
        const titleEl = document.getElementById('progressTitle');
        const messageEl = document.getElementById('progressMessage');
        
        if (indicator && titleEl && messageEl) {
            titleEl.textContent = title;
            messageEl.textContent = message;
            indicator.classList.remove('hidden');
            this.updateProgress(percent);
        }
    }

    hideProgress() {
        const indicator = document.getElementById('progressIndicator');
        if (indicator) {
            indicator.classList.add('hidden');
        }
    }

    updateProgress(percent) {
        const progressBar = document.getElementById('progressBar');
        const progressPercent = document.getElementById('progressPercent');
        
        if (progressBar && progressPercent) {
            progressBar.style.width = percent + '%';
            progressPercent.textContent = Math.round(percent) + '%';
            
            if (percent > 0 && percent < 100) {
                progressBar.classList.add('progress-bar-animated');
            } else {
                progressBar.classList.remove('progress-bar-animated');
            }
        }
    }

    async createBackup() {
        const backupType = document.getElementById('backupType')?.value || 'full';
        const backupName = document.getElementById('backupName')?.value.trim() || '';

        this.showProgress('Creating Backup', 'Initializing backup process...', 5);

        try {
            const response = await fetch(this.apiEndpoints.create, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken()
                },
                body: JSON.stringify({
                    backup_type: backupType,
                    backup_name: backupName
                })
            });

            this.updateProgress(30);

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            const result = await response.json();
            
            if (result.status === 'success') {
                this.updateProgress(60);
                
                // Poll for completion if job ID is provided
                if (result.data.job_id) {
                    await this.pollJobStatus(result.data.job_id, 'backup');
                } else {
                    this.updateProgress(100);
                }

                this.hideModal('createBackupModal');
                this.showNotification(
                    `Backup created successfully! File: ${result.data.filename}`, 
                    'success'
                );
                
                // Refresh data
                this.loadBackupHistory();
                this.loadStatistics();
            } else {
                throw new Error(result.message || 'Backup creation failed');
            }
        } catch (error) {
            console.error('Backup creation error:', error);
            this.showNotification(`Failed to create backup: ${error.message}`, 'error');
        } finally {
            this.hideProgress();
        }
    }

    async restoreFromUpload() {
        const fileInput = document.getElementById('backupFileInput');
        const restoreModeRadio = document.querySelector('input[name="restore_mode"]:checked');
        const restoreMode = restoreModeRadio ? restoreModeRadio.value : 'merge';

        if (!fileInput?.files[0]) {
            this.showNotification('Please select a backup file', 'error');
            return;
        }

        // Confirm dangerous operations
        if (restoreMode === 'replace') {
            const confirmed = confirm(
                'WARNING: Replace mode will delete ALL existing data!\n\n' +
                'This action cannot be undone. Are you absolutely sure you want to continue?'
            );
            if (!confirmed) return;
        }

        this.showProgress('Restoring Data', 'Uploading backup file...', 10);

        try {
            const formData = new FormData();
            formData.append('backup_file', fileInput.files[0]);
            formData.append('restore_mode', restoreMode);
            formData.append('csrfmiddlewaretoken', this.getCSRFToken());

            this.updateProgress(25);

            const response = await fetch(this.apiEndpoints.restore, {
                method: 'POST',
                body: formData
            });

            this.updateProgress(50);

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            const result = await response.json();
            
            if (result.status === 'success') {
                this.updateProgress(80);
                
                // Poll for completion if job ID is provided
                if (result.data.job_id) {
                    await this.pollJobStatus(result.data.job_id, 'restore');
                } else {
                    this.updateProgress(100);
                }

                this.hideModal('restoreUploadModal');
                
                const stats = result.data.result;
                this.showNotification(
                    `Restore completed successfully! Created: ${stats.created}, Updated: ${stats.updated}`, 
                    'success'
                );
                
                // Refresh data
                this.loadBackupHistory();
                this.loadStatistics();
            } else {
                throw new Error(result.message || 'Restore failed');
            }
        } catch (error) {
            console.error('Restore error:', error);
            this.showNotification(`Failed to restore: ${error.message}`, 'error');
        } finally {
            this.hideProgress();
        }
    }

    async restoreFromHistory(backupId) {
        const confirmed = confirm(
            'Are you sure you want to restore from this backup?\n\n' +
            'This will modify your current data. Existing records will be updated and new ones will be added.'
        );
        
        if (!confirmed) return;

        this.showProgress('Restoring Data', 'Processing backup from history...', 15);

        try {
            const response = await fetch(`${this.apiEndpoints.restoreHistory}${backupId}/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken()
                },
                body: JSON.stringify({
                    restore_mode: 'merge'
                })
            });

            this.updateProgress(40);

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            const result = await response.json();
            
            if (result.status === 'success') {
                this.updateProgress(70);
                
                // Poll for completion if job ID is provided
                if (result.data.job_id) {
                    await this.pollJobStatus(result.data.job_id, 'restore');
                } else {
                    this.updateProgress(100);
                }

                const stats = result.data.result;
                this.showNotification(
                    `Restore completed! Created: ${stats.created}, Updated: ${stats.updated}`, 
                    'success'
                );
                
                this.loadBackupHistory();
            } else {
                throw new Error(result.message || 'Restore failed');
            }
        } catch (error) {
            console.error('Restore error:', error);
            this.showNotification(`Failed to restore: ${error.message}`, 'error');
        } finally {
            this.hideProgress();
        }
    }

    async quickBackup(type) {
        this.showProgress('Quick Backup', `Creating ${type} backup...`, 10);

        try {
            const timestamp = new Date().toISOString().slice(0, 19).replace(/[:-]/g, '');
            const response = await fetch(this.apiEndpoints.create, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken()
                },
                body: JSON.stringify({
                    backup_type: type,
                    backup_name: `quick_${type}_${timestamp}`
                })
            });

            this.updateProgress(50);

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            const result = await response.json();
            
            if (result.status === 'success') {
                this.updateProgress(80);
                
                if (result.data.job_id) {
                    await this.pollJobStatus(result.data.job_id, 'backup');
                } else {
                    this.updateProgress(100);
                }

                this.showNotification(`${type} backup created successfully!`, 'success');
                this.loadBackupHistory();
                this.loadStatistics();
            } else {
                throw new Error(result.message || 'Quick backup failed');
            }
        } catch (error) {
            console.error('Quick backup error:', error);
            this.showNotification(`Failed to create ${type} backup: ${error.message}`, 'error');
        } finally {
            this.hideProgress();
        }
    }

    async pollJobStatus(jobId, jobType) {
        const maxAttempts = 30; // 30 seconds max
        let attempts = 0;

        return new Promise((resolve, reject) => {
            const poll = async () => {
                try {
                    const response = await fetch(`${this.apiEndpoints.status}${jobId}/`);
                    const result = await response.json();

                    if (result.status === 'success') {
                        const job = result.data;
                        
                        if (job.status === 'success') {
                            this.updateProgress(100);
                            resolve(job);
                            return;
                        } else if (job.status === 'failed') {
                            reject(new Error(job.error || 'Job failed'));
                            return;
                        } else if (job.status === 'running') {
                            // Update progress based on job type and time
                            const progress = Math.min(60 + (attempts * 2), 95);
                            this.updateProgress(progress);
                        }
                    }

                    attempts++;
                    if (attempts >= maxAttempts) {
                        reject(new Error('Job timeout'));
                        return;
                    }

                    setTimeout(poll, 1000);
                } catch (error) {
                    reject(error);
                }
            };

            poll();
        });
    }

    async loadBackupHistory() {
        if (this.isLoading) return;
        this.isLoading = true;

        try {
            const response = await fetch(
                `${this.apiEndpoints.history}?page=${this.currentPage}&limit=${this.itemsPerPage}`
            );
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            const result = await response.json();

            if (result.status === 'success') {
                this.renderBackupHistory(result.data.backups);
                this.updatePagination(result.data.pagination);
                this.totalItems = result.data.pagination.total;
            } else {
                throw new Error(result.message || 'Failed to load backup history');
            }
        } catch (error) {
            console.error('Failed to load backup history:', error);
            this.renderBackupHistoryError(error.message);
        } finally {
            this.isLoading = false;
        }
    }

    renderBackupHistory(backups) {
        const container = document.getElementById('backupHistoryContainer');
        if (!container) return;

        if (backups.length === 0) {
            container.innerHTML = `
                <div class="text-center py-16">
                    <div class="w-24 h-24 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-6">
                        <i class="fas fa-database text-4xl text-gray-400"></i>
                    </div>
                    <h3 class="text-2xl font-semibold text-gray-600 mb-3">No Backups Found</h3>
                    <p class="text-gray-500 mb-6">Create your first backup to get started with data protection</p>
                    <button onclick="backupManager.showModal('createBackupModal')" 
                            class="bg-gradient-to-r from-blue-500 to-indigo-600 hover:from-blue-600 hover:to-indigo-700 text-white px-6 py-3 rounded-xl transition-all duration-300 transform hover:scale-105">
                        <i class="fas fa-plus mr-2"></i>Create First Backup
                    </button>
                </div>
            `;
            return;
        }

        container.innerHTML = backups.map((backup, index) => {
            const date = new Date(backup.date);
            const isRecent = (Date.now() - date.getTime()) < 24 * 60 * 60 * 1000; // 24 hours
            
            return `
                <div class="bg-gray-50 rounded-xl p-4 border border-gray-200 hover:border-blue-300 hover:bg-blue-50 transition-all duration-300 hover-lift">
                    <div class="flex items-center justify-between">
                        <div class="flex items-center space-x-4">
                            <div class="w-12 h-12 bg-gradient-to-r ${backup.operation_type === 'backup' ? 'from-blue-500 to-indigo-600' : 'from-purple-500 to-indigo-600'} rounded-lg flex items-center justify-center">
                                <i class="fas fa-${backup.operation_type === 'backup' ? 'download' : 'upload'} text-white"></i>
                            </div>
                            <div>
                                <div class="flex items-center space-x-2">
                                    <h4 class="font-semibold text-gray-800">${backup.file_name}</h4>
                                    ${isRecent ? '<span class="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800"><i class="fas fa-circle mr-1 text-green-500"></i>Recent</span>' : ''}
                                </div>
                                <p class="text-sm text-gray-600">
                                    ${date.toLocaleString()} • 
                                    <span class="capitalize">${backup.operation_type}</span>
                                </p>
                            </div>
                        </div>
                        <div class="flex items-center space-x-2">
                            ${backup.operation_type === 'backup' ? `
                                <button onclick="backupManager.restoreFromHistory(${backup.id})" 
                                        class="px-4 py-2 bg-blue-500 hover:bg-blue-600 text-white rounded-lg transition-colors text-sm font-medium">
                                    <i class="fas fa-undo mr-1"></i>Restore
                                </button>
                            ` : ''}
                            <button onclick="backupManager.downloadBackup(${backup.id})" 
                                    class="px-4 py-2 bg-gray-500 hover:bg-gray-600 text-white rounded-lg transition-colors text-sm font-medium">
                                <i class="fas fa-download mr-1"></i>Download
                            </button>
                            <button onclick="backupManager.deleteBackup(${backup.id})" 
                                    class="px-4 py-2 bg-red-500 hover:bg-red-600 text-white rounded-lg transition-colors text-sm font-medium">
                                <i class="fas fa-trash"></i>
                            </button>
                        </div>
                    </div>
                </div>
            `;
        }).join('');
    }

    renderBackupHistoryError(errorMessage) {
        const container = document.getElementById('backupHistoryContainer');
        if (!container) return;

        container.innerHTML = `
            <div class="text-center py-16">
                <div class="w-24 h-24 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-6">
                    <i class="fas fa-exclamation-triangle text-4xl text-red-500"></i>
                </div>
                <h3 class="text-2xl font-semibold text-red-600 mb-3">Failed to Load Backups</h3>
                <p class="text-gray-600 mb-6">${errorMessage}</p>
                <button onclick="backupManager.loadBackupHistory()" 
                        class="bg-gradient-to-r from-blue-500 to-indigo-600 hover:from-blue-600 hover:to-indigo-700 text-white px-6 py-3 rounded-xl transition-all duration-300 transform hover:scale-105">
                    <i class="fas fa-refresh mr-2"></i>Try Again
                </button>
            </div>
        `;
    }

    updatePagination(pagination) {
        const container = document.getElementById('paginationContainer');
        const showingFrom = document.getElementById('showingFrom');
        const showingTo = document.getElementById('showingTo');
        const totalItems = document.getElementById('totalItems');
        const prevBtn = document.getElementById('prevPage');
        const nextBtn = document.getElementById('nextPage');

        if (container && pagination.total > 0) {
            container.classList.remove('hidden');
            
            const from = ((pagination.page - 1) * pagination.limit) + 1;
            const to = Math.min(pagination.page * pagination.limit, pagination.total);
            
            if (showingFrom) showingFrom.textContent = from;
            if (showingTo) showingTo.textContent = to;
            if (totalItems) totalItems.textContent = pagination.total;
            
            if (prevBtn) {
                prevBtn.disabled = pagination.page <= 1;
                prevBtn.classList.toggle('opacity-50', pagination.page <= 1);
            }
            if (nextBtn) {
                nextBtn.disabled = !pagination.has_next;
                nextBtn.classList.toggle('opacity-50', !pagination.has_next);
            }
        } else if (container) {
            container.classList.add('hidden');
        }
    }

    async loadStatistics() {
        try {
            const response = await fetch(`${this.apiEndpoints.history}?limit=1000`);
            
            if (response.ok) {
                const result = await response.json();
                if (result.status === 'success') {
                    const backups = result.data.backups.filter(b => b.operation_type === 'backup');
                    const totalBackups = backups.length;
                    
                    let lastBackup = 'Never';
                    if (backups.length > 0) {
                        const lastBackupDate = new Date(backups[0].date);
                        const now = new Date();
                        const diffMinutes = Math.floor((now - lastBackupDate) / (1000 * 60));
                        
                        if (diffMinutes < 1) {
                            lastBackup = 'Just now';
                        } else if (diffMinutes < 60) {
                            lastBackup = `${diffMinutes} minute${diffMinutes > 1 ? 's' : ''} ago`;
                        } else if (diffMinutes < 1440) {
                            const diffHours = Math.floor(diffMinutes / 60);
                            lastBackup = `${diffHours} hour${diffHours > 1 ? 's' : ''} ago`;
                        } else {
                            const diffDays = Math.floor(diffMinutes / 1440);
                            lastBackup = `${diffDays} day${diffDays > 1 ? 's' : ''} ago`;
                        }
                    }
                    
                    const storageUsed = `${(totalBackups * 0.15).toFixed(1)} GB`;
                    
                    document.getElementById('totalBackups').textContent = totalBackups;
                    document.getElementById('lastBackup').textContent = lastBackup;
                    document.getElementById('storageUsed').textContent = storageUsed;
                }
            }
        } catch (error) {
            console.error('Failed to load statistics:', error);
            document.getElementById('totalBackups').textContent = '-';
            document.getElementById('lastBackup').textContent = 'Unknown';
            document.getElementById('storageUsed').textContent = '-';
        }
    }

    async loadRecentActivity() {
        try {
            const container = document.getElementById('recentActivity');
            if (!container) return;

            const response = await fetch(`${this.apiEndpoints.history}?limit=5`);
            if (response.ok) {
                const result = await response.json();
                if (result.status === 'success') {
                    const activities = result.data.backups.map(backup => {
                        const date = new Date(backup.date);
                        const now = new Date();
                        const diffMinutes = Math.floor((now - date) / (1000 * 60));
                        
                        let timeAgo;
                        if (diffMinutes < 1) {
                            timeAgo = 'Just now';
                        } else if (diffMinutes < 60) {
                            timeAgo = `${diffMinutes} minute${diffMinutes > 1 ? 's' : ''} ago`;
                        } else if (diffMinutes < 1440) {
                            const diffHours = Math.floor(diffMinutes / 60);
                            timeAgo = `${diffHours} hour${diffHours > 1 ? 's' : ''} ago`;
                        } else {
                            const diffDays = Math.floor(diffMinutes / 1440);
                            timeAgo = `${diffDays} day${diffDays > 1 ? 's' : ''} ago`;
                        }
                        
                        return {
                            type: backup.operation_type,
                            message: backup.operation_type === 'backup' ? 'Backup completed' : 'Data restored',
                            time: timeAgo,
                            icon: backup.operation_type === 'backup' ? 'download' : 'upload',
                            color: backup.operation_type === 'backup' ? 'green' : 'blue'
                        };
                    });

                    container.innerHTML = activities.map(activity => `
                        <div class="flex items-center space-x-3 p-2 rounded-lg hover:bg-gray-50">
                            <div class="w-8 h-8 bg-${activity.color}-100 rounded-full flex items-center justify-center">
                                <i class="fas fa-${activity.icon} text-${activity.color}-600 text-sm"></i>
                            </div>
                            <div class="flex-1">
                                <p class="text-sm font-medium text-gray-800">${activity.message}</p>
                                <p class="text-xs text-gray-500">${activity.time}</p>
                            </div>
                        </div>
                    `).join('');
                }
            }
        } catch (error) {
            console.error('Failed to load recent activity:', error);
            const container = document.getElementById('recentActivity');
            if (container) {
                container.innerHTML = '<p class="text-sm text-gray-500 text-center py-4">Unable to load recent activity</p>';
            }
        }
    }

    startPeriodicRefresh() {
        // Refresh statistics every 30 seconds
        setInterval(() => {
            if (!this.isLoading) {
                this.loadStatistics();
                this.loadRecentActivity();
            }
        }, 30000);
    }

    showNotification(message, type = 'info', duration = 5000) {
        const container = document.getElementById('messages-container') || this.createNotificationContainer();
        const notification = document.createElement('div');
        
        const colors = {
            success: 'from-green-500 to-emerald-600',
            error: 'from-red-500 to-red-600',
            info: 'from-blue-500 to-indigo-600',
            warning: 'from-yellow-500 to-orange-600'
        };

        const icons = {
            success: 'fa-check-circle',
            error: 'fa-exclamation-circle',
            info: 'fa-info-circle',
            warning: 'fa-exclamation-triangle'
        };

        notification.className = `bg-gradient-to-r ${colors[type]} text-white p-4 rounded-xl shadow-lg animate-slide-in max-w-md mb-3 transform transition-all duration-300`;
        notification.innerHTML = `
            <div class="flex items-center justify-between">
                <div class="flex items-center">
                    <i class="fas ${icons[type]} mr-3 text-lg"></i>
                    <span class="font-medium">${message}</span>
                </div>
                <button onclick="this.parentElement.parentElement.remove()" 
                        class="ml-4 text-white hover:text-gray-200 transition-colors">
                    <i class="fas fa-times"></i>
                </button>
            </div>
        `;

        container.appendChild(notification);

        // Auto-remove after duration
        setTimeout(() => {
            if (notification.parentNode) {
                notification.style.opacity = '0';
                notification.style.transform = 'translateX(100%)';
                setTimeout(() => notification.remove(), 300);
            }
        }, duration);
    }

    createNotificationContainer() {
        const container = document.createElement('div');
        container.id = 'messages-container';
        container.className = 'fixed top-4 right-4 z-50 space-y-2';
        document.body.appendChild(container);
        return container;
    }

    async downloadBackup(backupId) {
        try {
            const link = document.createElement('a');
            link.href = `${this.apiEndpoints.download}${backupId}/`;
            link.download = '';
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
            
            this.showNotification('Download started', 'success');
        } catch (error) {
            console.error('Download error:', error);
            this.showNotification('Failed to download backup', 'error');
        }
    }

    async deleteBackup(backupId) {
        const confirmed = confirm(
            'Are you sure you want to delete this backup?\n\n' +
            'This action cannot be undone.'
        );
        
        if (!confirmed) return;

        try {
            const response = await fetch(`/backup/api/delete/${backupId}/`, {
                method: 'DELETE',
                headers: {
                    'X-CSRFToken': this.getCSRFToken()
                }
            });

            if (response.ok) {
                this.showNotification('Backup deleted successfully', 'success');
                this.loadBackupHistory();
                this.loadStatistics();
            } else {
                throw new Error('Failed to delete backup');
            }
        } catch (error) {
            console.error('Delete error:', error);
            this.showNotification('Failed to delete backup', 'error');
        }
    }

    async exportHistory() {
        try {
            const link = document.createElement('a');
            link.href = '/backup/api/export/history/';
            link.download = 'backup_history.csv';
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
            
            this.showNotification('Export started', 'success');
        } catch (error) {
            console.error('Export error:', error);
            this.showNotification('Failed to export history', 'error');
        }
    }

    getCSRFToken() {
        const token = document.querySelector('[name=csrfmiddlewaretoken]')?.value;
        if (!token) {
            console.warn('CSRF token not found');
        }
        return token || '';
    }
}

// Initialize backup manager when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    window.backupManager = new BackupManager();
});

// Export for module systems
if (typeof module !== 'undefined' && module.exports) {
    module.exports = BackupManager;
}