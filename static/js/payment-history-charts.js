// Payment History Charts - 2025 Advanced Implementation
class PaymentHistoryCharts {
    constructor() {
        this.charts = {};
        this.colors = {
            primary: 'rgb(59, 130, 246)',
            success: 'rgb(34, 197, 94)',
            warning: 'rgb(251, 191, 36)',
            danger: 'rgb(239, 68, 68)',
            info: 'rgb(168, 85, 247)'
        };
        this.init();
    }

    init() {
        // Initialize Chart.js with global defaults
        Chart.defaults.font.family = 'Inter, system-ui, sans-serif';
        Chart.defaults.color = '#6B7280';
        Chart.defaults.plugins.legend.display = false;
        
        this.initPaymentTrendChart();
        this.initPaymentStatusChart();
        this.initDailyCollectionChart();
    }

    initPaymentTrendChart() {
        const ctx = document.getElementById('paymentTrendChart');
        if (!ctx) return;

        this.charts.trend = new Chart(ctx, {
            type: 'line',
            data: {
                labels: [],
                datasets: [{
                    label: 'Daily Collections',
                    data: [],
                    borderColor: this.colors.primary,
                    backgroundColor: this.colors.primary + '20',
                    borderWidth: 3,
                    fill: true,
                    tension: 0.4,
                    pointBackgroundColor: this.colors.primary,
                    pointBorderColor: '#ffffff',
                    pointBorderWidth: 2,
                    pointRadius: 6,
                    pointHoverRadius: 8
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                interaction: {
                    intersect: false,
                    mode: 'index'
                },
                plugins: {
                    tooltip: {
                        backgroundColor: 'rgba(0, 0, 0, 0.8)',
                        titleColor: '#ffffff',
                        bodyColor: '#ffffff',
                        borderColor: this.colors.primary,
                        borderWidth: 1,
                        cornerRadius: 8,
                        displayColors: false,
                        callbacks: {
                            label: (context) => {
                                return `Collections: ₹${context.parsed.y.toLocaleString()}`;
                            }
                        }
                    }
                },
                scales: {
                    x: {
                        grid: {
                            display: false
                        },
                        border: {
                            display: false
                        }
                    },
                    y: {
                        beginAtZero: true,
                        grid: {
                            color: '#F3F4F6'
                        },
                        border: {
                            display: false
                        },
                        ticks: {
                            callback: function(value) {
                                return '₹' + value.toLocaleString();
                            }
                        }
                    }
                },
                elements: {
                    point: {
                        hoverBackgroundColor: this.colors.primary
                    }
                }
            }
        });
    }

    initPaymentStatusChart() {
        const ctx = document.getElementById('paymentStatusChart');
        if (!ctx) return;

        this.charts.status = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: ['Successful', 'Pending', 'Failed'],
                datasets: [{
                    data: [0, 0, 0],
                    backgroundColor: [
                        this.colors.success,
                        this.colors.warning,
                        this.colors.danger
                    ],
                    borderWidth: 0,
                    cutout: '70%'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: true,
                        position: 'bottom',
                        labels: {
                            padding: 20,
                            usePointStyle: true,
                            pointStyle: 'circle'
                        }
                    },
                    tooltip: {
                        backgroundColor: 'rgba(0, 0, 0, 0.8)',
                        titleColor: '#ffffff',
                        bodyColor: '#ffffff',
                        cornerRadius: 8,
                        callbacks: {
                            label: (context) => {
                                const label = context.label;
                                const value = context.parsed;
                                const total = context.dataset.data.reduce((a, b) => a + b, 0);
                                const percentage = ((value / total) * 100).toFixed(1);
                                return `${label}: ${value} (${percentage}%)`;
                            }
                        }
                    }
                }
            }
        });
    }

    initDailyCollectionChart() {
        const ctx = document.getElementById('dailyCollectionChart');
        if (!ctx) return;

        this.charts.daily = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: [],
                datasets: [{
                    label: 'Daily Collections',
                    data: [],
                    backgroundColor: this.colors.success + '80',
                    borderColor: this.colors.success,
                    borderWidth: 1,
                    borderRadius: 6,
                    borderSkipped: false
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    tooltip: {
                        backgroundColor: 'rgba(0, 0, 0, 0.8)',
                        titleColor: '#ffffff',
                        bodyColor: '#ffffff',
                        cornerRadius: 8,
                        callbacks: {
                            label: (context) => {
                                return `Amount: ₹${context.parsed.y.toLocaleString()}`;
                            }
                        }
                    }
                },
                scales: {
                    x: {
                        grid: {
                            display: false
                        },
                        border: {
                            display: false
                        }
                    },
                    y: {
                        beginAtZero: true,
                        grid: {
                            color: '#F3F4F6'
                        },
                        border: {
                            display: false
                        },
                        ticks: {
                            callback: function(value) {
                                return '₹' + (value / 1000) + 'K';
                            }
                        }
                    }
                }
            }
        });
    }

    async updateTrendChart(range = 'month') {
        try {
            const response = await fetch(`/reports/api/payment-trend/?range=${range}`);
            const data = await response.json();
            
            if (this.charts.trend) {
                this.charts.trend.data.labels = data.labels;
                this.charts.trend.data.datasets[0].data = data.values;
                this.charts.trend.update('active');
            }
        } catch (error) {
            console.error('Failed to update trend chart:', error);
        }
    }

    async updateStatusChart() {
        try {
            const response = await fetch('/reports/api/payment-status/');
            const data = await response.json();
            
            if (this.charts.status) {
                this.charts.status.data.datasets[0].data = [
                    data.successful || 0,
                    data.pending || 0,
                    data.failed || 0
                ];
                this.charts.status.update('active');
            }
        } catch (error) {
            console.error('Failed to update status chart:', error);
        }
    }

    async updateDailyChart(days = 7) {
        try {
            const response = await fetch(`/reports/api/daily-collections/?days=${days}`);
            const data = await response.json();
            
            if (this.charts.daily) {
                this.charts.daily.data.labels = data.labels;
                this.charts.daily.data.datasets[0].data = data.values;
                this.charts.daily.update('active');
            }
        } catch (error) {
            console.error('Failed to update daily chart:', error);
        }
    }

    // Animation helpers
    animateValue(element, start, end, duration = 1000) {
        const startTimestamp = performance.now();
        
        const step = (timestamp) => {
            const elapsed = timestamp - startTimestamp;
            const progress = Math.min(elapsed / duration, 1);
            
            const current = start + (end - start) * this.easeOutCubic(progress);
            element.textContent = Math.floor(current).toLocaleString();
            
            if (progress < 1) {
                requestAnimationFrame(step);
            }
        };
        
        requestAnimationFrame(step);
    }

    easeOutCubic(t) {
        return 1 - Math.pow(1 - t, 3);
    }

    // Utility methods
    formatCurrency(amount) {
        return new Intl.NumberFormat('en-IN', {
            style: 'currency',
            currency: 'INR',
            minimumFractionDigits: 0,
            maximumFractionDigits: 0
        }).format(amount);
    }

    formatDate(date) {
        return new Intl.DateTimeFormat('en-IN', {
            day: '2-digit',
            month: 'short'
        }).format(new Date(date));
    }

    // Export functionality
    exportChartAsPNG(chartName) {
        const chart = this.charts[chartName];
        if (!chart) return;

        const link = document.createElement('a');
        link.download = `${chartName}-chart-${new Date().toISOString().split('T')[0]}.png`;
        link.href = chart.toBase64Image();
        link.click();
    }

    // Responsive handling
    handleResize() {
        Object.values(this.charts).forEach(chart => {
            if (chart) {
                chart.resize();
            }
        });
    }

    // Cleanup
    destroy() {
        Object.values(this.charts).forEach(chart => {
            if (chart) {
                chart.destroy();
            }
        });
        this.charts = {};
    }
}

// Date filter utilities
function setDateFilter(range) {
    const today = new Date();
    let fromDate, toDate;

    switch (range) {
        case 'today':
            fromDate = toDate = today.toISOString().split('T')[0];
            break;
        case 'week':
            fromDate = new Date(today.setDate(today.getDate() - 7)).toISOString().split('T')[0];
            toDate = new Date().toISOString().split('T')[0];
            break;
        case 'month':
            fromDate = new Date(today.setMonth(today.getMonth() - 1)).toISOString().split('T')[0];
            toDate = new Date().toISOString().split('T')[0];
            break;
        case 'overdue':
            // Set to show overdue payments (before today)
            toDate = new Date().toISOString().split('T')[0];
            fromDate = new Date(today.setFullYear(today.getFullYear() - 1)).toISOString().split('T')[0];
            break;
    }

    // Update form inputs
    const fromInput = document.getElementById('date_from');
    const toInput = document.getElementById('date_to');
    
    if (fromInput) fromInput.value = fromDate;
    if (toInput) toInput.value = toDate;

    // Submit form or trigger HTMX request
    const form = document.querySelector('form[method="GET"]');
    if (form) {
        form.submit();
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    // Initialize charts
    window.paymentCharts = new PaymentHistoryCharts();
    
    // Handle window resize
    window.addEventListener('resize', () => {
        if (window.paymentCharts) {
            window.paymentCharts.handleResize();
        }
    });
    
    // Auto-refresh charts every 5 minutes
    setInterval(() => {
        if (window.paymentCharts) {
            window.paymentCharts.updateTrendChart();
            window.paymentCharts.updateStatusChart();
            window.paymentCharts.updateDailyChart();
        }
    }, 300000); // 5 minutes
});

// Export for global use
window.setDateFilter = setDateFilter;