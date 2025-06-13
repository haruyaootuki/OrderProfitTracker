// Profit Analysis JavaScript
class ProfitAnalyzer {
    constructor() {
        this.currentData = null;
        
        this.initializeEventListeners();
        this.loadProjects();
        this.initializeDateInputs();
    }
    
    initializeEventListeners() {
        // Analysis form submission
        document.getElementById('analysisForm').addEventListener('submit', (e) => {
            e.preventDefault();
            this.loadProfitData();
        });
        
        // コスト入力の変更を監視
        const costInputs = ['employee_cost', 'bp_cost'];
        costInputs.forEach(inputId => {
            const input = document.getElementById(inputId);
            if (input) {
                input.addEventListener('input', (e) => {
                    // 小数点以下を削除
                    e.target.value = e.target.value.replace(/[^0-9]/g, '');
                    this.calculateRealTimeProfit();
                });
            }
        });
    }
    
    initializeDateInputs() {
        // デフォルトで現在年月を設定
        const today = new Date();
        const year = today.getFullYear();
        const month = (today.getMonth() + 1).toString().padStart(2, '0');
        const currentMonth = `${year}-${month}`;
        
        document.getElementById('startDate').value = currentMonth;
        document.getElementById('endDate').value = currentMonth;
    }
    
    async loadProjects() {
        try {
            const response = await fetch('/api/projects', {
                headers: {
                    'X-CSRFToken': document.querySelector('meta[name=csrf-token]').getAttribute('content')
                }
            });
            
            if (!response.ok) {
                throw new Error('プロジェクト一覧の取得に失敗しました');
            }
            
            const data = await response.json();
            const select = document.getElementById('projectSelect');
            
            // 既存のオプションをクリア（最初の2つの静的オプションを除く）
            while (select.options.length > 2) {
                select.remove(2);
            }
            
            // プロジェクトを追加
            data.projects.forEach(project => {
                const option = document.createElement('option');
                option.value = project;
                option.textContent = project;
                select.appendChild(option);
            });
            
        } catch (error) {
            console.error('Error loading projects:', error);
            this.showError('プロジェクト一覧の読み込み中にエラーが発生しました');
        }
    }
    
    async loadProfitData() {
        try {
            const project = document.getElementById('projectSelect').value;
            const startDate = document.getElementById('startDate').value;
            const endDate = document.getElementById('endDate').value;
            const employeeCost = document.getElementById('employee_cost').value.replace(/[^0-9]/g, '');
            const bpCost = document.getElementById('bp_cost').value.replace(/[^0-9]/g, '');
            
            if (!project || !startDate || !endDate) {
                this.showError('プロジェクトと期間を選択してください');
                return;
            }
            
            // コストのバリデーション
            if (isNaN(employeeCost) || isNaN(bpCost)) {
                this.showError('コストは整数で入力してください');
                return;
            }
            
            try {
                this.showProfitLoading();
                
                const response = await fetch(`/api/profit-data?project=${encodeURIComponent(project)}&start_date=${startDate}&end_date=${endDate}&employee_cost=${employeeCost}&bp_cost=${bpCost}`, {
                    headers: {
                        'X-CSRFToken': document.querySelector('meta[name=csrf-token]').getAttribute('content')
                    }
                });
                
                if (!response.ok) {
                    const errorData = await response.json();
                    throw new Error(errorData.error || 'データの取得に失敗しました');
                }
                
                const data = await response.json();
                this.currentData = data;
                this.renderProfitData(data);
            } finally {
                this.hideProfitLoading();
            }
            
        } catch (error) {
            console.error('Error loading profit data:', error);
            this.showError(error.message || '利益データの読み込み中にエラーが発生しました');
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
        const projectNameDisplay = data.project_name === 'all' ? 'すべてのプロジェクト' : data.project_name;
        document.getElementById('periodInfo').textContent = `${projectNameDisplay} (${this.formatDate(data.start_date)} 〜 ${this.formatDate(data.end_date)})`;
        document.getElementById('totalRevenue').textContent = `¥${data.total_revenue.toLocaleString()}`;
        document.getElementById('totalCost').textContent = `¥${data.total_cost.toLocaleString()}`;
        document.getElementById('totalProfit').textContent = `¥${data.profit.toLocaleString()}`;
        
        // Update profit rate and styling
        const profitRateElement = document.getElementById('profitRate');

        if (typeof data.profit_rate === 'number') {
            const profitRate = parseFloat(data.profit_rate.toFixed(1));
            profitRateElement.textContent = `${profitRate}%`;

            // 利益が0未満の場合は赤色、それ以外は緑色に設定
            if (data.profit < 0) {
                profitRateElement.classList.remove('text-success');
                profitRateElement.classList.add('text-danger');
            } else {
                profitRateElement.classList.remove('text-danger');
                profitRateElement.classList.add('text-success');
            }
        } else {
            profitRateElement.textContent = '0%';
            profitRateElement.classList.remove('text-danger');
            profitRateElement.classList.add('text-success');
        }
    }
    
    calculateRealTimeProfit() {
        if (!this.currentData) return;
        
        const employeeCost = parseInt(document.getElementById('employee_cost').value.replace(/[^0-9]/g, '')) || 0;
        const bpCost = parseInt(document.getElementById('bp_cost').value.replace(/[^0-9]/g, '')) || 0;
        const totalCost = employeeCost + bpCost;
        const profit = this.currentData.total_revenue - totalCost;
        
        // 利益率の計算（確実に数値型として計算）
        let profitRate = 0;
        if (this.currentData.total_revenue > 0) {
            profitRate = (profit / this.currentData.total_revenue) * 100;
        }
        
        // Update the display with new calculations
        this.currentData.employee_cost = employeeCost;
        this.currentData.bp_cost = bpCost;
        this.currentData.total_cost = totalCost;
        this.currentData.profit = profit;
        this.currentData.profit_rate = profitRate;
        
        this.renderProfitData(this.currentData);
    }
    
    showProfitLoading() {
        try {
            const loadingOverlay = document.getElementById('loadingOverlay');
            if (loadingOverlay) {
                loadingOverlay.classList.remove('d-none');
            }
        } catch (error) {
            console.warn('Loading overlay not found:', error);
        }
    }
    
    hideProfitLoading() {
        try {
            const loadingOverlay = document.getElementById('loadingOverlay');
            if (loadingOverlay) {
                loadingOverlay.classList.add('d-none');
            }
        } catch (error) {
            console.warn('Loading overlay not found:', error);
        }
    }
    
    showSuccess(message) {
        this.showAlert(message, 'success');
    }
    
    showError(message) {
        try {
            const alertContainer = document.getElementById('alertContainer');
            if (!alertContainer) {
                console.warn('Alert container not found');
                return;
            }
            
            const alert = document.createElement('div');
            alert.className = 'alert alert-danger alert-dismissible fade show';
            alert.innerHTML = `
                ${this.escapeHtml(message)}
                <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
            `;
            alertContainer.appendChild(alert);
            
            setTimeout(() => {
                alert.classList.add('d-none');
                alert.remove();
            }, 5000);
        } catch (error) {
            console.error('Error displaying error alert:', error);
        }
    }
    
    showAlert(message, type) {
        const alertContainer = document.getElementById('alertContainer');
        if (!alertContainer) return;

        const alertDiv = document.createElement('div');
        alertDiv.className = `alert alert-${type} alert-dismissible fade show`;
        alertDiv.setAttribute('role', 'alert');
        alertDiv.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
        `;
        alertContainer.appendChild(alertDiv);

        setTimeout(() => {
            if (alertDiv && alertDiv.parentNode) {
                alertDiv.parentNode.removeChild(alertDiv);
            }
        }, 5000);
    }
    
    formatCurrency(amount) {
        return `¥${amount.toLocaleString()}`;
    }
    
    formatDate(dateStr) {
        // YYYY-MM 形式の文字列を YYYY年MM月 に変換
        const parts = dateStr.split('-');
        if (parts.length === 2) {
            return `${parts[0]}年${parts[1]}月`;
        } else {
            // それ以外の形式の場合はそのまま返すか、エラー処理
            return dateStr;
        }
    }
    
    escapeHtml(text) {
        const div = document.createElement('div');
        div.appendChild(document.createTextNode(text));
        return div.innerHTML;
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new ProfitAnalyzer();
});
