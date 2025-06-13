// Orders management JavaScript
class OrderManager {
    constructor() {
        this.editingOrderId = null;
        this.deleteOrderId = null;
        
        this.initializeTabulator();
        this.initializeEventListeners();
    }
    
    initializeTabulator() {
        // Tabulatorテーブルの初期化
        this.table = new Tabulator("#orders-table", {
            ajaxURL: "/api/orders",
            ajaxConfig: {
                method: "GET",
                headers: {
                    "X-CSRFToken": document.querySelector('meta[name=csrf-token]').getAttribute('content')
                },
            },
            layout: "fitColumns",
            responsiveLayout: "hide",
            history: true,
            pagination: "remote", // サーバーサイドページネーション
            paginationSize: 20, // 1ページあたりの行数
            paginationSizeSelector: [10, 20, 50, 100], // ページサイズ選択
            movableColumns: true, // カラムの並べ替えを許可
            resizableColumns: true, // カラムのリサイズを許可
            tooltips: true, // ツールチップ表示
            placeholder: "データがありません", // データがない場合のメッセージ
            columns: [
                { title: "受注日", field: "order_date", hozAlign: "center", sorter: "date" },
                {
                    title: "受注金額", field: "order_amount", hozAlign: "right", sorter: "number",
                    formatter: function (cell, formatterParams, onRendered) {
                        return '¥' + parseFloat(cell.getValue()).toLocaleString();
                    }
                },
                {
                    title: "請求金額", field: "invoiced_amount", hozAlign: "right", sorter: "number",
                    formatter: function (cell, formatterParams, onRendered) {
                        return '¥' + parseFloat(cell.getValue()).toLocaleString();
                    }
                },
                {
                    title: "売上金額", field: "sales_amount", hozAlign: "right", sorter: "number",
                    formatter: function (cell, formatterParams, onRendered) {
                        return '¥' + parseFloat(cell.getValue()).toLocaleString();
                    }
                },
                { title: "顧客名", field: "customer_name", sorter: "string" },
                { title: "案件名", field: "project_name", sorter: "string" },
                { title: "契約形態", field: "contract_type", sorter: "string" },
                { title: "確度", field: "sales_stage", sorter: "string" },
                { title: "請求月", field: "billing_month", hozAlign: "center", sorter: "date" },
                {
                    title: "仕掛", field: "work_in_progress", hozAlign: "center", formatter: "tickCross",
                    formatterParams: { allowEmpty: true, allowTruthy: true }
                },
                { title: "備考", field: "description", sorter: "string" },
                {
                    title: "操作", field: "actions", hozAlign: "center", formatter: "html", width: 120, headerSort: false,
                    formatter: (cell, formatterParams, onRendered) => {
                        const orderId = cell.getRow().getData().id;
                        return `
                            <button type="button" class="btn btn-sm btn-outline-primary btn-action edit-btn" data-id="${orderId}" title="編集">
                                <i class="fas fa-edit"></i>
                            </button>
                            <button type="button" class="btn btn-sm btn-outline-danger btn-action delete-btn" data-id="${orderId}" title="削除">
                                <i class="fas fa-trash"></i>
                            </button>
                        `;
                    },
                    cellClick: (e, cell) => {
                        const target = e.target.closest('button');
                        if (!target) return;

                        const orderId = target.dataset.id;
                        if (target.classList.contains('edit-btn')) {
                            this.editOrder(orderId);
                        } else if (target.classList.contains('delete-btn')) {
                            this.confirmDelete(orderId);
                        }
                    },
                },
            ],
            ajaxResponse: function (url, params, response) {
                return response.orders; // 受注データの配列を直接返す
            },
        });
    }
    
    initializeEventListeners() {
        // 検索機能 (Tabulatorのフィルターを使用)
        document.getElementById('searchInput').addEventListener('input', (e) => {
            // 顧客名とプロジェクト名で検索
            this.table.setFilter([
                { field: "customer_name", type: "like", value: e.target.value },
                { field: "project_name", type: "like", value: e.target.value },
            ]);
        });

        // クリアボタン
        document.getElementById('clearSearchBtn').addEventListener('click', () => {
            document.getElementById('searchInput').value = '';
            this.table.clearFilter();
        });

        // 更新ボタン
        document.getElementById('refreshOrdersBtn').addEventListener('click', () => {
            this.table.replaceData(); // 現在のフィルターとソートを維持してデータを再読み込み
        });
        
        // Order form submission
        document.getElementById('orderForm').addEventListener('submit', (e) => {
            e.preventDefault();
            this.saveOrder();
        });
        
        // Modal events
        document.getElementById('orderModal').addEventListener('hidden.bs.modal', () => {
            this.resetForm();
        });
        
        // Delete confirmation
        document.getElementById('confirmDeleteBtn').addEventListener('click', () => {
            this.deleteOrder();
        });
    }
    
    async editOrder(orderId) {
        try {
            const row = this.table.getRow(orderId);
            if (!row) {
                this.showError('受注データが見つかりません');
                return;
            }
            const order = row.getData();
            
            this.editingOrderId = orderId;
            this.populateForm(order);
            
            // Update modal title
            document.getElementById('orderModalTitle').innerHTML = 
                '<i class="fas fa-edit me-2"></i>受注編集';
            
            // Show modal
            const modal = new bootstrap.Modal(document.getElementById('orderModal'));
            modal.show();
            
        } catch (error) {
            console.error('Error editing order:', error);
            this.showError('受注データの取得中にエラーが発生しました');
        }
    }
    
    populateForm(order) {
        document.getElementById('id').value = order.id;
        document.getElementById('customer_name').value = order.customer_name;
        document.getElementById('project_name').value = order.project_name;
        document.getElementById('sales_amount').value = order.sales_amount;
        document.getElementById('order_amount').value = order.order_amount;
        document.getElementById('invoiced_amount').value = order.invoiced_amount;
        document.getElementById('order_date').value = order.order_date;
        document.getElementById('contract_type').value = order.contract_type || '';
        document.getElementById('sales_stage').value = order.sales_stage || '';
        document.getElementById('billing_month').value = order.billing_month || '';
        document.getElementById('work_in_progress').checked = order.work_in_progress;
        document.getElementById('description').value = order.description || '';
    }
    
    async saveOrder() {
        try {
            const form = document.getElementById('orderForm');
            const formData = new FormData(form);
            const submitBtn = document.getElementById('orderSubmitBtn');
            
            // Show loading state
            submitBtn.disabled = true;
            submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>保存中...';
            
            // Clear previous validation errors
            this.clearValidationErrors();
            
            const url = this.editingOrderId ? 
                `/api/orders/${this.editingOrderId}` : '/api/orders';
            const method = this.editingOrderId ? 'PUT' : 'POST';
            
            const response = await fetch(url, {
                method: method,
                headers: {
                    'X-CSRFToken': document.querySelector('meta[name=csrf-token]').getAttribute('content')
                },
                body: formData
            });
            
            const result = await response.json();
            
            if (!response.ok) {
                if (response.status === 400 && result.errors) {
                    this.showValidationErrors(result.errors);
                } else {
                    throw new Error(result.error || '保存中にエラーが発生しました');
                }
            } else {
                this.showSuccess(result.message);
                this.hideModal('orderModal');
                this.table.replaceData(); // データ保存後にテーブルを更新
            }
        } catch (error) {
            console.error('Error saving order:', error);
            this.showError(error.message || '受注の保存中にエラーが発生しました');
        } finally {
            // Hide loading state
            const submitBtn = document.getElementById('orderSubmitBtn');
            submitBtn.disabled = false;
            submitBtn.innerHTML = '<i class="fas fa-save me-2"></i>保存';
        }
    }
    
    confirmDelete(orderId) {
        this.deleteOrderId = orderId;
        const modal = new bootstrap.Modal(document.getElementById('deleteModal'));
        modal.show();
    }
    
    async deleteOrder() {
        try {
            const response = await fetch(`/api/orders/${this.deleteOrderId}`, {
                method: 'DELETE',
                headers: {
                    'X-CSRFToken': document.querySelector('meta[name=csrf-token]').getAttribute('content')
                }
            });
            
            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.error || '削除に失敗しました');
            }
            
            const result = await response.json();
            this.showSuccess(result.message);
            this.hideModal('deleteModal');
            this.table.replaceData(); // 削除後にテーブルを更新
            
        } catch (error) {
            console.error('Error deleting order:', error);
            this.showError(error.message || '受注の削除中にエラーが発生しました');
        } finally {
            this.deleteOrderId = null;
        }
    }
    
    resetForm() {
        document.getElementById('orderForm').reset();
        document.getElementById('id').value = ''; // IDをクリア
        this.editingOrderId = null;
        
        // Update modal title to '新規受注登録'
        document.getElementById('orderModalTitle').innerHTML = 
            '<i class="fas fa-plus me-2"></i>新規受注登録';
        
        this.clearValidationErrors();
    }
    
    clearValidationErrors() {
        document.querySelectorAll('.is-invalid').forEach(el => {
            el.classList.remove('is-invalid');
        });
        document.querySelectorAll('.invalid-feedback').forEach(el => {
            el.textContent = '';
        });
    }
    
    showValidationErrors(errors) {
        for (const fieldName in errors) {
            const input = document.getElementById(fieldName);
            if (input) {
                input.classList.add('is-invalid');
                const feedback = input.nextElementSibling; // Assuming invalid-feedback is next sibling
                if (feedback && feedback.classList.contains('invalid-feedback')) {
                    feedback.textContent = errors[fieldName][0];
                }
            }
        }
    }
    
    hideModal(modalId) {
        const modalElement = document.getElementById(modalId);
        if (modalElement) {
            const modal = bootstrap.Modal.getInstance(modalElement);
            if (modal) {
                modal.hide();
            }
        }
    }
    
    showSuccess(message) {
        this.showAlert(message, 'success');
    }
    
    showError(message) {
        this.showAlert(message, 'danger');
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

    formatNumber(num) {
        return num.toLocaleString();
    }
    
    formatDate(dateString) {
        if (!dateString) return '';
        const date = new Date(dateString);
        return date.toLocaleDateString('ja-JP');
    }
    
    escapeHtml(text) {
        const div = document.createElement('div');
        div.appendChild(document.createTextNode(text));
        return div.innerHTML;
    }
}

// Initialize the OrderManager when the DOM is fully loaded
document.addEventListener('DOMContentLoaded', () => {
    window.orderManager = new OrderManager();
    // グローバル関数は不要になるので削除
    // function clearSearch() { orderManager.clearSearch(); }
    // function refreshOrders() { orderManager.refreshOrders(); }
});

