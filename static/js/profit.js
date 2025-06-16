// Profit Analysis JavaScript
class ProfitAnalyzer {
    constructor() {
        this.currentData = null;
        
        this.initializeEventListeners();
        this.loadProjects();
        // this.initializeDateInputs();
    }
    
    initializeEventListeners() {
        // Analysis form submission
        document.getElementById('analysisForm').addEventListener('submit', (e) => {
            e.preventDefault();
            this.loadProfitData();
        });

        // コスト入力のフォーマット処理を統一
        const setupCostInput = (inputElement) => {
            // 初期値を0に設定し、フォーマット
            if (!inputElement.value) {
                inputElement.value = '0';
            } else {
                inputElement.value = parseInt(inputElement.value.replace(/,/g, '')).toLocaleString('ja-JP');
            }

            // 入力時の処理
            inputElement.addEventListener('input', (e) => {
                // 数値とカンマ以外の文字を除去
                let value = e.target.value.replace(/[^\d,]/g, '');
                // カンマを一旦除去して数値に変換し、最大値を制限
                let numValue = parseInt(value.replace(/,/g, '')) || 0;
                if (numValue > 100000000000) { // 1000億に制限
                    numValue = 100000000000;
                }
                // カンマ区切りを適用（入力途中でも適用）
                e.target.value = numValue.toLocaleString('ja-JP', { maximumFractionDigits: 0 });

                // 関連する表示データの更新（リアルタイム）
                if (this.currentData) {
                    this.renderProfitData(this.currentData);
                }
            });

            // フォーカスを失った時のフォーマット
            inputElement.addEventListener('blur', () => {
                let numValue = parseInt(inputElement.value.replace(/,/g, '')) || 0;
                inputElement.value = numValue.toLocaleString('ja-JP', { maximumFractionDigits: 0 });
            });

            // フォーカスを得た時の処理 (カンマを除去して編集しやすくする)
            inputElement.addEventListener('focus', () => {
                const value = inputElement.value.replace(/,/g, '');
                inputElement.value = value === '0' ? '' : value;
            });
        };

        const employeeCostInput = document.getElementById('employee_cost_input');
        const bpCostInput = document.getElementById('bp_cost_input');

        if (employeeCostInput) {
            setupCostInput(employeeCostInput);
        }
        if (bpCostInput) {
            setupCostInput(bpCostInput);
        }
    }
    
    // initializeDateInputs() {
    //     // デフォルトで現在年月を設定 -> YYYY-MM-DD形式に変更
    //     const today = new Date();
    //     const year = today.getFullYear();
    //     const month = (today.getMonth() + 1).toString().padStart(2, '0');

    //     // 月の最初の日と最後の日を計算
    //     const firstDayOfMonth = new Date(year, today.getMonth(), 1);
    //     const lastDayOfMonth = new Date(year, today.getMonth() + 1, 0);

    //     document.getElementById('startDate').value = firstDayOfMonth.toISOString().split('T')[0];
    //     document.getElementById('endDate').value = lastDayOfMonth.toISOString().split('T')[0];
    // }
    
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
            const project_name = document.getElementById('projectSelect').value;
            const start_date = document.getElementById('startDate').value;
            const end_date = document.getElementById('endDate').value;

            if (!project_name || !start_date || !end_date) {
                this.showError('プロジェクト名、開始日、終了日は必須です');
                return;
            }
            // `employeeCost` と `bpCost` の取得とバリデーションを削除

            try {
                this.showProfitLoading();

                // URLからコストパラメータを削除
                const response = await fetch(`/api/profit-data?project_name=${encodeURIComponent(project_name)}&start_date=${start_date}&end_date=${end_date}`, {
                    headers: {
                        'X-CSRFToken': document.querySelector('meta[name=csrf-token]').getAttribute('content')
                    }
                });

                if (!response.ok) {
                    const errorData = await response.json();
                    throw new Error(errorData.error || 'データの取得に失敗しました');
                }

                const data = await response.json();
                this.currentData = data; // 最新データを保存
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
        const profitDataDisplay = document.getElementById('profitDataDisplay');
        const noProfitData = document.getElementById('noProfitData');

        // if (data.total_sales_amount === 0 && data.total_order_amount === 0 && data.total_invoiced_amount === 0) {
        //     profitDataDisplay.style.display = 'none';
        //     noProfitData.style.display = 'block';
        //     return;
        // }

        profitDataDisplay.style.display = 'block';
        noProfitData.style.display = 'none';

        const projectName = document.getElementById('projectSelect').value;
        const startDate = document.getElementById('startDate').value;
        const endDate = document.getElementById('endDate').value;

        const projectNameDisplay = projectName === 'all' ? 'すべての案件' : projectName;
        document.getElementById('periodInfo').textContent = `${projectNameDisplay} (${this.formatDate(startDate)} 〜 ${this.formatDate(endDate)})`;

        document.getElementById('totalSalesAmount').textContent = `¥${data.total_sales_amount.toLocaleString()}`;
        document.getElementById('totalOrderAmount').textContent = `¥${data.total_order_amount.toLocaleString()}`;
        document.getElementById('totalInvoicedAmount').textContent = `¥${data.total_invoiced_amount.toLocaleString()}`;

        // 手動入力された社員コストとBPコストを取得し、計算
        const employeeCost = parseInt(document.getElementById('employee_cost_input').value.replace(/,/g, '')) || 0;
        const bpCost = parseInt(document.getElementById('bp_cost_input').value.replace(/,/g, '')) || 0;

        const totalCost = employeeCost + bpCost;
        const profit = data.total_sales_amount - totalCost;

        let profitRate = 0;
        if (data.total_sales_amount > 0) {
            profitRate = (profit / data.total_sales_amount) * 100;
        }

        document.getElementById('calculatedTotalCost').textContent = `¥${totalCost.toLocaleString()}`;
        document.getElementById('calculatedProfit').textContent = `¥${profit.toLocaleString()}`;

        const profitRateElement = document.getElementById('calculatedProfitRate');
        profitRateElement.textContent = `${profitRate.toFixed(1)}%`;

        if (profit < 0) {
            profitRateElement.classList.remove('text-success');
            profitRateElement.classList.add('text-danger');
        } else {
            profitRateElement.classList.remove('text-danger');
            profitRateElement.classList.add('text-success');
        }
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
        // YYYY-MM-DD 形式の日付文字列を YYYY年M月D日 形式に変換
        const [year, month, day] = dateStr.split('-');
        return `${parseInt(year)}年${parseInt(month)}月${parseInt(day)}日`;
    }
    
    escapeHtml(text) {
        const div = document.createElement('div');
        div.appendChild(document.createTextNode(text));
        return div.innerHTML;
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    const analyzer = new ProfitAnalyzer(); // ProfitAnalyzerのインスタンスを一つだけ作成

    // コスト入力フィールドのイベントリスナーを再設定
    const employeeCostInput = document.getElementById('employee_cost_input');
    const bpCostInput = document.getElementById('bp_cost_input');

    if (employeeCostInput) {
        employeeCostInput.addEventListener('input', () => {
            if (analyzer.currentData) {
                analyzer.renderProfitData(analyzer.currentData);
            }
        });
    }

    if (bpCostInput) {
        bpCostInput.addEventListener('input', () => {
            if (analyzer.currentData) {
                analyzer.renderProfitData(analyzer.currentData);
            }
        });
    }
});
