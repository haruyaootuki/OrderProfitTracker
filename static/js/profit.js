// Profit Analysis JavaScript
class ProfitAnalyzer {
    constructor() {
        this.currentData = null;
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
    
    showError(message) {
        // エラーメッセージは既にサーバー側でフラッシュメッセージとして設定されているため、
        // ここではページをリロードしてフラッシュメッセージを表示する
        window.location.reload();
    }
    
    formatDate(dateStr) {
        // YYYY-MM-DD 形式の日付文字列を YYYY年M月D日 形式に変換
        const [year, month, day] = dateStr.split('-');
        return `${parseInt(year)}年${parseInt(month)}月${parseInt(day)}日`;
    }
    
    async init() {
        this.initializeEventListeners();
        await this.loadProjects();
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', async () => {
    const analyzer = new ProfitAnalyzer(); // ProfitAnalyzerのインスタンスを一つだけ作成
    await analyzer.init(); // 非同期初期化メソッドを呼び出す

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
