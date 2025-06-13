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

        // コスト入力の変更を監視 (変更)
        const employeeCostInput = document.getElementById('employee_cost_input');
        const bpCostInput = document.getElementById('bp_cost_input');

        if (employeeCostInput) {
            employeeCostInput.addEventListener('input', (e) => {
                e.target.value = e.target.value.replace(/[^0-9]/g, '');
                if (this.currentData) {
                    this.renderProfitData(this.currentData);
                }
            });
        }

        if (bpCostInput) {
            bpCostInput.addEventListener('input', (e) => {
                e.target.value = e.target.value.replace(/[^0-9]/g, '');
                if (this.currentData) {
                    this.renderProfitData(this.currentData);
                }
            });
        }
    }
    
    initializeDateInputs() {
        // デフォルトで現在年月を設定 -> YYYY-MM-DD形式に変更
        const today = new Date();
        const year = today.getFullYear();
        const month = (today.getMonth() + 1).toString().padStart(2, '0');

        // 月の最初の日と最後の日を計算
        const firstDayOfMonth = new Date(year, today.getMonth(), 1);
        const lastDayOfMonth = new Date(year, today.getMonth() + 1, 0);

        document.getElementById('startDate').value = firstDayOfMonth.toISOString().split('T')[0];
        document.getElementById('endDate').value = lastDayOfMonth.toISOString().split('T')[0];
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
        // `profitData` を `profitDataDisplay` に変更
        const profitDataDisplay = document.getElementById('profitDataDisplay');
        const noProfitData = document.getElementById('noProfitData');

        // 売上、受注、請求金額のいずれかが0の場合は非表示 (条件を追加)
        if (data.total_sales_amount === 0 && data.total_order_amount === 0 && data.total_invoiced_amount === 0) {
            profitDataDisplay.style.display = 'none';
            noProfitData.style.display = 'block';
            return;
        }

        profitDataDisplay.style.display = 'block';
        noProfitData.style.display = 'none';

        // Update values
        const projectName = document.getElementById('projectSelect').value;
        const startDate = document.getElementById('startDate').value;
        const endDate = document.getElementById('endDate').value;

        const projectNameDisplay = projectName === 'all' ? 'すべてのプロジェクト' : projectName;
        document.getElementById('periodInfo').textContent = `${projectNameDisplay} (${this.formatDate(startDate)} 〜 ${this.formatDate(endDate)})`;

        // 新しい要素IDに合わせて更新
        document.getElementById('totalSalesAmount').textContent = `¥${data.total_sales_amount.toLocaleString()}`;
        document.getElementById('totalOrderAmount').textContent = `¥${data.total_order_amount.toLocaleString()}`;
        document.getElementById('totalInvoicedAmount').textContent = `¥${data.total_invoiced_amount.toLocaleString()}`;

        // 手動入力された社員コストとBPコストを取得し、計算
        const employeeCost = parseInt(document.getElementById('employee_cost_input').value) || 0;
        const bpCost = parseInt(document.getElementById('bp_cost_input').value) || 0;

        const totalCost = employeeCost + bpCost;
        const profit = data.total_sales_amount - totalCost; // 売上からコストを引く

        let profitRate = 0;
        if (data.total_sales_amount > 0) {
            profitRate = (profit / data.total_sales_amount) * 100;
        }

        // 新しい要素IDに合わせて更新
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

    // コスト入力フィールドのイベントリスナーを再設定 (変更)
    const employeeCostInput = document.getElementById('employee_cost_input');
    const bpCostInput = document.getElementById('bp_cost_input');

    if (employeeCostInput) {
        employeeCostInput.addEventListener('input', () => {
            // インスタンスを再利用してrenderProfitDataを呼び出す
            if (analyzer.currentData) {
                analyzer.renderProfitData(analyzer.currentData);
            }
        });
    }

    if (bpCostInput) {
        bpCostInput.addEventListener('input', () => {
            // インスタンスを再利用してrenderProfitDataを呼び出す
            if (analyzer.currentData) {
                analyzer.renderProfitData(analyzer.currentData);
            }
        });
    }
});

document.addEventListener('DOMContentLoaded', function() {
    const analysisForm = document.getElementById('analysisForm');
    const projectSelect = document.getElementById('projectSelect');
    const startDateInput = document.getElementById('startDate');
    const endDateInput = document.getElementById('endDate');
    const employeeCostInput = document.getElementById('employee_cost_input');
    const bpCostInput = document.getElementById('bp_cost_input');
    const loadingOverlay = document.getElementById('loadingOverlay');
    const noProfitData = document.getElementById('noProfitData');
    const profitDataDisplay = document.getElementById('profitDataDisplay');
    const periodInfo = document.getElementById('periodInfo');
    const totalSalesAmount = document.getElementById('totalSalesAmount');
    const totalOrderAmount = document.getElementById('totalOrderAmount');
    const totalInvoicedAmount = document.getElementById('totalInvoicedAmount');
    const manualCost = document.getElementById('manualCost');
    const calculatedTotalCost = document.getElementById('calculatedTotalCost');
    const calculatedProfit = document.getElementById('calculatedProfit');
    const calculatedProfitRate = document.getElementById('calculatedProfitRate');

    // プロジェクト一覧を取得
    fetch('/api/projects')
        .then(response => response.json())
        .then(data => {
            data.projects.forEach(project => {
                const option = document.createElement('option');
                option.value = project;
                option.textContent = project;
                projectSelect.appendChild(option);
            });
        })
        .catch(error => {
            console.error('Error fetching projects:', error);
            showAlert('プロジェクト一覧の取得に失敗しました', 'danger');
        });

    // フォーム送信時の処理
    analysisForm.addEventListener('submit', function(e) {
        e.preventDefault();
        
        const projectName = projectSelect.value;
        const startDate = startDateInput.value;
        const endDate = endDateInput.value;
        const employeeCost = parseInt(employeeCostInput.value) || 0;
        const bpCost = parseInt(bpCostInput.value) || 0;

        if (!projectName || !startDate || !endDate) {
            showAlert('プロジェクト、開始日、終了日をすべて入力してください', 'warning');
            return;
        }

        // ローディング表示
        loadingOverlay.classList.remove('d-none');
        noProfitData.style.display = 'none';
        profitDataDisplay.style.display = 'none';

        // データを取得
        fetch(`/api/profit-data?project_name=${encodeURIComponent(projectName)}&start_date=${startDate}&end_date=${endDate}`)
            .then(response => response.json())
            .then(data => {
                if (data.error) {
                    throw new Error(data.error);
                }

                // 期間情報を表示
                periodInfo.textContent = `${projectName} (${startDate} 〜 ${endDate})`;

                // 金額を表示
                totalSalesAmount.textContent = formatCurrency(data.total_sales_amount);
                totalOrderAmount.textContent = formatCurrency(data.total_order_amount);
                totalInvoicedAmount.textContent = formatCurrency(data.total_invoiced_amount);

                // コストと利益を計算
                const totalManualCost = employeeCost + bpCost;
                manualCost.textContent = formatCurrency(totalManualCost);
                calculatedTotalCost.textContent = formatCurrency(totalManualCost);
                
                const profit = data.total_sales_amount - totalManualCost;
                calculatedProfit.textContent = formatCurrency(profit);
                
                const profitRate = data.total_sales_amount > 0 
                    ? (profit / data.total_sales_amount * 100).toFixed(1)
                    : 0;
                calculatedProfitRate.textContent = `${profitRate}%`;

                // 結果を表示
                profitDataDisplay.style.display = 'block';
            })
            .catch(error => {
                console.error('Error:', error);
                showAlert(error.message || 'データの取得に失敗しました', 'danger');
                noProfitData.style.display = 'block';
            })
            .finally(() => {
                loadingOverlay.classList.add('d-none');
            });
    });

    // 通貨フォーマット関数
    function formatCurrency(amount) {
        return '¥' + amount.toLocaleString();
    }

    // アラート表示関数
    function showAlert(message, type) {
        const alertContainer = document.getElementById('alertContainer');
        const alert = document.createElement('div');
        alert.className = `alert alert-${type} alert-dismissible fade show`;
        alert.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
        `;
        alertContainer.appendChild(alert);
        setTimeout(() => alert.remove(), 5000);
    }
});
