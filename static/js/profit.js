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
        
        if (data.total_revenue === 0) {
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
        const totalCost = data.employee_cost + data.bp_cost;
        
        // Destroy existing chart
        if (this.costChart) {
            this.costChart.destroy();
        }
        
        this.costChart = new Chart(ctx, {
            type: 'pie',
            data: {
                labels: ['社員原価', 'BP原価'],
                datasets: [{
                    data: [data.employee_cost, data.bp_cost],
                    backgroundColor: [
                        'rgba(255, 99, 132, 0.8)',
                        'rgba(54, 162, 235, 0.8)'
                    ],
                    borderColor: [
                        'rgba(255, 99, 132, 1)',
                        'rgba(54, 162, 235, 1)'
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
    
    calculateRealTimeProfit() {
        if (!this.currentData) return;
        
        const employeeCost = parseFloat(document.getElementById('employee_cost').value) || 0;
        const bpCost = parseFloat(document.getElementById('bp_cost').value) || 0;
        const totalCost = employeeCost + bpCost;
        const profit = this.currentData.total_revenue - totalCost;
        const profitRate = this.currentData.total_revenue > 0 ? 
            (profit / this.currentData.total_revenue * 100) : 0;
        
        // Update the display with new calculations
        this.currentData.employee_cost = employeeCost;
        this.currentData.bp_cost = bpCost;
        this.currentData.total_cost = totalCost;
        this.currentData.profit = profit;
        this.currentData.profit_rate = profitRate;
        
        this.renderProfitData(this.currentData);
        this.renderCharts(this.currentData);
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
        const alertDiv = document.createElement('div');
        alertDiv.className = `alert alert-${type} alert-dismissible fade show`;
        alertDiv.innerHTML = `
            ${this.escapeHtml(message)}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        const container = document.querySelector('.container');
        container.insertBefore(alertDiv, container.firstChild);
        
        // Auto-dismiss after 5 seconds
        setTimeout(() => {
            alertDiv.remove();
        }, 5000);
    }
    
    formatCurrency(amount) {
        return '¥' + new Intl.NumberFormat('ja-JP').format(Math.round(amount));
    }
    
    formatDate(dateStr) {
        if (!dateStr) return '';
        const date = new Date(dateStr);
        return date.toLocaleDateString('ja-JP');
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
