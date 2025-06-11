// Profit Analysis JavaScript
class ProfitAnalyzer {
    constructor() {
        this.profitChart = null;
        this.costChart = null;
        this.currentData = null;
        
        this.initializeEventListeners();
        this.loadProfitData();
    }
    
    initializeEventListeners() {
        // Cost form submission
        document.getElementById('costForm').addEventListener('submit', (e) => {
            e.preventDefault();
            this.saveCostData();
        });
        
        // Real-time calculation on input change
        const costInputs = ['employee_cost', 'bp_cost'];
        costInputs.forEach(inputId => {
            const input = document.getElementById(inputId);
            if (input) {
                input.addEventListener('input', () => {
                    this.calculateRealTimeProfit();
                });
            }
        });
    }
    
    async loadProfitData() {
        try {
            this.showProfitLoading();
            
            const response = await fetch('/api/profit-data', {
                headers: {
                    'X-CSRFToken': document.querySelector('meta[name=csrf-token]').getAttribute('content')
                }
            });
            
            if (!response.ok) {
                throw new Error('データの取得に失敗しました');
            }
            
            const data = await response.json();
            this.currentData = data;
            this.renderProfitData(data);
            this.renderCharts(data);
            this.hideProfitLoading();
            
        } catch (error) {
            console.error('Error loading profit data:', error);
            this.showError('利益データの読み込み中にエラーが発生しました');
            this.hideProfitLoading();
        }
    }
    
    renderProfitData(data) {
        const profitData = document.getElementById('profitData');
        const noProfitData = document.getElementById('noProfitData');
        
        if (data.total_revenue === 0 && data.total_cost === 0) {
            profitData.style.display = 'none';
            noProfitData.style.display = 'block';
            return;
        }
        
        profitData.style.display = 'block';
        noProfitData.style.display = 'none';
        
        // Update values
        document.getElementById('totalRevenue').textContent = this.formatCurrency(data.total_revenue);
        document.getElementById('totalCost').textContent = this.formatCurrency(data.total_cost);
        document.getElementById('totalProfit').textContent = this.formatCurrency(data.profit);
        document.getElementById('employeeCost').textContent = this.formatCurrency(data.employee_cost);
        document.getElementById('bpCost').textContent = this.formatCurrency(data.bp_cost);
        
        // Update profit rate and styling
        const profitRate = data.profit_rate;
        const profitRateElement = document.getElementById('profitRate');
        const totalProfitElement = document.getElementById('totalProfit');
        const progressBar = document.getElementById('profitProgressBar');
        
        profitRateElement.textContent = `${profitRate.toFixed(1)}%`;
        
        // Color coding based on profit
        if (data.profit > 0) {
            totalProfitElement.className = 'mb-2 profit-positive';
            progressBar.className = 'progress-bar bg-success';
        } else if (data.profit < 0) {
            totalProfitElement.className = 'mb-2 profit-negative';
            progressBar.className = 'progress-bar bg-danger';
        } else {
            totalProfitElement.className = 'mb-2 profit-neutral';
            progressBar.className = 'progress-bar bg-warning';
        }
        
        // Update progress bar
        const progressPercentage = Math.min(Math.abs(profitRate), 100);
        progressBar.style.width = `${progressPercentage}%`;
        
        // Update period info
        const periodInfo = document.getElementById('periodInfo');
        if (data.period_start && data.period_end) {
            periodInfo.textContent = `期間: ${this.formatDate(data.period_start)} 〜 ${this.formatDate(data.period_end)}`;
        } else {
            periodInfo.textContent = '期間情報なし';
        }
    }
    
    renderCharts(data) {
        this.renderProfitChart(data);
        this.renderCostBreakdownChart(data);
    }
    
    renderProfitChart(data) {
        const ctx = document.getElementById('profitChart').getContext('2d');
        
        // Destroy existing chart
        if (this.profitChart) {
            this.profitChart.destroy();
        }
        
        this.profitChart = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: ['売上', '原価', '利益'],
                datasets: [{
                    data: [data.total_revenue, data.total_cost, Math.max(0, data.profit)],
                    backgroundColor: [
                        'rgba(54, 162, 235, 0.8)',
                        'rgba(255, 99, 132, 0.8)',
                        'rgba(75, 192, 192, 0.8)'
                    ],
                    borderColor: [
                        'rgba(54, 162, 235, 1)',
                        'rgba(255, 99, 132, 1)',
                        'rgba(75, 192, 192, 1)'
                    ],
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    title: {
                        display: true,
                        text: '売上・原価・利益比較',
                        color: '#fff'
                    },
                    legend: {
                        display: false
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            callback: function(value) {
                                return '¥' + new Intl.NumberFormat('ja-JP').format(value);
                            },
                            color: '#fff'
                        },
                        grid: {
                            color: 'rgba(255, 255, 255, 0.1)'
                        }
                    },
                    x: {
                        ticks: {
                            color: '#fff'
                        },
                        grid: {
                            color: 'rgba(255, 255, 255, 0.1)'
                        }
                    }
                }
            }
        });
    }
    
    renderCostBreakdownChart(data) {
        const ctx = document.getElementById('costBreakdownChart').getContext('2d');
        
        // Destroy existing chart
        if (this.costChart) {
            this.costChart.destroy();
        }
        
        const totalCost = data.employee_cost + data.bp_cost;
        
        if (totalCost === 0) {
            // Show empty state
            ctx.clearRect(0, 0, ctx.canvas.width, ctx.canvas.height);
            ctx.fillStyle = '#6c757d';
            ctx.font = '16px Arial';
            ctx.textAlign = 'center';
            ctx.fillText('原価データがありません', ctx.canvas.width / 2, ctx.canvas.height / 2);
            return;
        }
        
        this.costChart = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: ['社員原価', 'BP原価'],
                datasets: [{
                    data: [data.employee_cost, data.bp_cost],
                    backgroundColor: [
                        'rgba(255, 206, 86, 0.8)',
                        'rgba(153, 102, 255, 0.8)'
                    ],
                    borderColor: [
                        'rgba(255, 206, 86, 1)',
                        'rgba(153, 102, 255, 1)'
                    ],
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    title: {
                        display: true,
                        text: '原価内訳',
                        color: '#fff'
                    },
                    legend: {
                        position: 'bottom',
                        labels: {
                            color: '#fff'
                        }
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                const label = context.label || '';
                                const value = context.parsed;
                                const percentage = ((value / totalCost) * 100).toFixed(1);
                                return `${label}: ¥${new Intl.NumberFormat('ja-JP').format(value)} (${percentage}%)`;
                            }
                        }
                    }
                }
            }
        });
    }
    
    async saveCostData() {
        try {
            const form = document.getElementById('costForm');
            const formData = new FormData(form);
            const submitBtn = form.querySelector('button[type="submit"]');
            
            // Show loading state
            submitBtn.disabled = true;
            submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>保存中...';
            
            // Clear previous validation errors
            this.clearValidationErrors();
            
            const response = await fetch('/api/cost-data', {
                method: 'POST',
                headers: {
                    'X-CSRFToken': document.querySelector('meta[name=csrf-token]').getAttribute('content')
                },
                body: formData
            });
            
            const data = await response.json();
            
            if (!response.ok) {
                if (data.errors) {
                    this.showValidationErrors(data.errors);
                } else {
                    throw new Error(data.error || '保存に失敗しました');
                }
                return;
            }
            
            // Success
            this.showSuccess(data.message);
            this.loadProfitData(); // Reload profit data
            
        } catch (error) {
            console.error('Error saving cost data:', error);
            this.showError(error.message || '保存中にエラーが発生しました');
        } finally {
            // Reset button state
            const submitBtn = document.getElementById('costForm').querySelector('button[type="submit"]');
            submitBtn.disabled = false;
            submitBtn.innerHTML = '<i class="fas fa-save me-2"></i>原価データ保存';
        }
    }
    
    calculateRealTimeProfit() {
        if (!this.currentData) return;
        
        const employeeCost = parseFloat(document.getElementById('employee_cost').value) || 0;
        const bpCost = parseFloat(document.getElementById('bp_cost').value) || 0;
        const totalCost = employeeCost + bpCost;
        const profit = this.currentData.total_revenue - totalCost;
        const profitRate = this.currentData.total_revenue > 0 ? 
            (profit / this.currentData.total_revenue * 100) : 0;
        
        // Update preview (could add a preview section if needed)
        console.log('Real-time calculation:', { profit, profitRate });
    }
    
    clearValidationErrors() {
        const errorElements = document.querySelectorAll('.invalid-feedback');
        errorElements.forEach(el => el.textContent = '');
        
        const invalidInputs = document.querySelectorAll('.is-invalid');
        invalidInputs.forEach(input => input.classList.remove('is-invalid'));
    }
    
    showValidationErrors(errors) {
        for (const [field, messages] of Object.entries(errors)) {
            const input = document.getElementById(field);
            if (input) {
                input.classList.add('is-invalid');
                const feedback = input.parentNode.querySelector('.invalid-feedback');
                if (feedback) {
                    feedback.textContent = messages.join(', ');
                }
            }
        }
    }
    
    showProfitLoading() {
        document.getElementById('loadingProfit').style.display = 'block';
        document.getElementById('profitData').style.display = 'none';
        document.getElementById('noProfitData').style.display = 'none';
    }
    
    hideProfitLoading() {
        document.getElementById('loadingProfit').style.display = 'none';
    }
    
    showSuccess(message) {
        this.showAlert(message, 'success');
    }
    
    showError(message) {
        this.showAlert(message, 'danger');
    }
    
    showAlert(message, type) {
        const alertHtml = `
            <div class="alert alert-${type} alert-dismissible fade show" role="alert">
                ${this.escapeHtml(message)}
                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
            </div>
        `;
        
        const container = document.querySelector('main .container');
        container.insertAdjacentHTML('afterbegin', alertHtml);
        
        // Auto-hide after 5 seconds
        setTimeout(() => {
            const alert = container.querySelector('.alert');
            if (alert) {
                const bsAlert = bootstrap.Alert.getInstance(alert);
                if (bsAlert) {
                    bsAlert.close();
                }
            }
        }, 5000);
    }
    
    formatCurrency(amount) {
        return '¥' + new Intl.NumberFormat('ja-JP').format(Math.round(amount));
    }
    
    formatDate(dateString) {
        const date = new Date(dateString);
        return new Intl.DateTimeFormat('ja-JP', {
            year: 'numeric',
            month: '2-digit',
            day: '2-digit'
        }).format(date);
    }
    
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.profitAnalyzer = new ProfitAnalyzer();
});
