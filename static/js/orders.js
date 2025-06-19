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
            layout: "fitDataTable",
            responsiveLayout: "hide",
            history: true,
            pagination: "remote",
            paginationSize: 20,
            paginationSizeSelector: [10, 20, 50, 100],
            movableColumns: true,
            resizableColumns: true,
            tooltips: true,
            placeholder: "データがありません",
            footerElement: "<div class='tabulator-footer'></div>",
            columns: [
                { title: "受注日",field: "order_date", hozAlign: "center", width: 100, frozen: true, sorter: "date",
                    sorterParams: {
                        format: "yyyy-MM-dd",
                    },
                    formatter: function (cell) {
                        return luxon.DateTime.fromISO(cell.getValue()).toFormat("yyyy/MM/dd")
                    }
                },
                {
                    title: "受注金額", field: "order_amount", hozAlign: "right", sorter: "number", width: 120, frozen: true,
                    formatter: function (cell, formatterParams, onRendered) {
                        const value = parseInt(cell.getValue()) || 0;
                        return '¥' + value.toLocaleString('ja-JP', { maximumFractionDigits: 0 });
                    },
                    bottomCalc: function(values) {
                        const sum = values.reduce((acc, val) => acc + (parseInt(val) || 0), 0);
                        return '¥' + sum.toLocaleString('ja-JP', { maximumFractionDigits: 0 });
                    },
                    bottomCalcFormatter: function(cell) {
                        return cell.getValue();
                    }
                },
                {
                    title: "請求金額", field: "invoiced_amount", hozAlign: "right", sorter: "number", width: 120, frozen: true,
                    formatter: function (cell, formatterParams, onRendered) {
                        const value = parseInt(cell.getValue()) || 0;
                        return '¥' + value.toLocaleString('ja-JP', { maximumFractionDigits: 0 });
                    },
                    bottomCalc: function(values) {
                        const sum = values.reduce((acc, val) => acc + (parseInt(val) || 0), 0);
                        return '¥' + sum.toLocaleString('ja-JP', { maximumFractionDigits: 0 });
                    },
                    bottomCalcFormatter: function(cell) {
                        return cell.getValue();
                    }
                },
                {
                    title: "売上金額", field: "sales_amount", hozAlign: "right", sorter: "number", width: 120, frozen: true,
                    formatter: function (cell, formatterParams, onRendered) {
                        const value = parseInt(cell.getValue()) || 0;
                        return '¥' + value.toLocaleString('ja-JP', { maximumFractionDigits: 0 });
                    },
                    bottomCalc: function(values) {
                        const sum = values.reduce((acc, val) => acc + (parseInt(val) || 0), 0);
                        return '¥' + sum.toLocaleString('ja-JP', { maximumFractionDigits: 0 });
                    },
                    bottomCalcFormatter: function(cell) {
                        return cell.getValue();
                    }
                },
                { title: "顧客名", field: "customer_name", sorter: "string", width: 120 },
                { title: "案件名", field: "project_name", sorter: "string", width: 200 },
                { title: "契約", field: "contract_type", sorter: "string", width: 70 },
                { title: "確度", field: "sales_stage", sorter: "string", width: 70 },
                {
                    title: "請求日",
                    field: "billing_month",
                    hozAlign: "center",
                    sorter: "date",
                    width: 100,
                    sorterParams: {
                        format: "yyyy-MM-dd",
                        alignEmptyValues: "bottom"
                    },
                    formatter: function (cell) {
                        const value = cell.getValue();
                        if (!value) return '';
                        return luxon.DateTime.fromISO(value).toFormat("yyyy/MM/dd");
                    }
                },
                {
                    title: "仕掛", field: "work_in_progress", hozAlign: "center", formatter: "tickCross", width: 70,
                    formatterParams: { allowEmpty: true, allowTruthy: true }
                },
                { title: "備考", field: "description", sorter: "string", width: 250 },
                {
                    title: "操作", field: "actions", hozAlign: "center", width: 120, headerSort: false,
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
                return response.orders;
            },
        });
    }
    
    initializeEventListeners() {
        // 検索フォームの送信イベント
        document.getElementById('searchForm').addEventListener('submit', (e) => {
            e.preventDefault();
            this.performSearch();
        });

        // 検索条件クリアボタン
        document.getElementById('clearSearchBtn').addEventListener('click', () => {
            document.getElementById('searchForm').reset();
            this.table.clearFilter();
        });
        
        // Modal events
        document.getElementById('orderModal').addEventListener('hidden.bs.modal', () => {
            this.resetForm();
        });
        
        // Delete confirmation
        document.getElementById('confirmDeleteBtn').addEventListener('click', () => {
            this.deleteOrder();
        });

        this.initializeFormHandlers();
    }
    
    initializeFormHandlers() {
        const form = document.getElementById('orderForm');
        const modal = document.getElementById('orderModal');
        const modalTitle = document.getElementById('orderModalTitle');
        const submitBtn = document.getElementById('orderSubmitBtn');
        const deleteBtn = document.getElementById('confirmDeleteBtn');

        // 数値入力フィールドのフォーマット処理
        const formatNumberInput = (input) => {
            // 数値以外を除去（カンマは許可）
            let value = input.value.replace(/[^\d,]/g, '');
            // カンマを除去して数値に変換
            let numValue = parseInt(value.replace(/,/g, '')) || 0;
            // 10億を超える場合は10億に制限
            if (numValue > 1000000000) {
                numValue = 1000000000;
            }
            // カンマ区切りを適用
            input.value = numValue.toLocaleString('ja-JP', { maximumFractionDigits: 0 });
        };

        // 数値入力フィールドのイベントリスナーを設定
        const numberInputs = ['sales_amount', 'order_amount', 'invoiced_amount'];
        numberInputs.forEach(id => {
            const input = document.getElementById(id);
            if (input) {
                // 初期値を0に設定
                if (!input.value) {
                    input.value = '0';
                } else {
                    // 既存の値がある場合はカンマ区切りで表示
                    input.value = parseInt(input.value).toLocaleString('ja-JP', { maximumFractionDigits: 0 });
                }

                // 入力時の処理
                input.addEventListener('input', (e) => {
                    // 入力中の値はそのまま表示（カンマは許可）
                    e.target.value = e.target.value.replace(/[^\d,]/g, '');
                });

                // フォーカスを失った時のフォーマット
                input.addEventListener('blur', () => {
                    formatNumberInput(input);
                    // 空の場合は0を表示
                    if (!input.value) {
                        input.value = '0';
                    }
                });

                // フォーカスを得た時の処理
                input.addEventListener('focus', () => {
                    // カンマを除去して数値のみを表示
                    const value = input.value.replace(/,/g, '');
                    input.value = value === '0' ? '' : value;
                });
            }
        });

        // フォーム送信時の処理
        form.addEventListener('submit', async (e) => {
            e.preventDefault();
            await this.saveOrder();
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
        // 数値フィールドの初期表示を改善
        const formatAmount = (amount) => {
            const value = parseInt(amount) || 0;
            return value.toLocaleString('ja-JP', { maximumFractionDigits: 0 });
        };
        document.getElementById('sales_amount').value = formatAmount(order.sales_amount);
        document.getElementById('order_amount').value = formatAmount(order.order_amount);
        document.getElementById('invoiced_amount').value = formatAmount(order.invoiced_amount);
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
            
            // 数値フィールドのカンマを除去
            const numberFields = ['sales_amount', 'order_amount', 'invoiced_amount'];
            numberFields.forEach(field => {
                if (formData[field]) {
                    formData[field] = formData[field].replace(/,/g, '');
                }
            });
            
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

    performSearch() {
        const filters = [];
        
        // 受注日範囲検索
        const orderDateFrom = document.getElementById('orderDateFrom').value;
        const orderDateTo = document.getElementById('orderDateTo').value;
        if (orderDateFrom) {
            filters.push({
                field: "order_date",
                type: ">=",
                value: orderDateFrom
            });
        }
        if (orderDateTo) {
            filters.push({
                field: "order_date",
                type: "<=",
                value: orderDateTo
            });
        }

        // 顧客名検索
        const customerName = document.getElementById('searchCustomerName').value;
        if (customerName) {
            filters.push({
                field: "customer_name",
                type: "like",
                value: customerName
            });
        }

        // 案件名検索
        const projectName = document.getElementById('searchProjectName').value;
        if (projectName) {
            filters.push({
                field: "project_name",
                type: "like",
                value: projectName
            });
        }

        // 契約検索
        const contractType = document.getElementById('searchContractType').value;
        if (contractType) {
            filters.push({
                field: "contract_type",
                type: "like",
                value: contractType
            });
        }

        // 確度検索
        const salesStage = document.getElementById('searchSalesStage').value;
        if (salesStage) {
            filters.push({
                field: "sales_stage",
                type: "like",
                value: salesStage
            });
        }

        // 請求日範囲検索
        const billingDateFrom = document.getElementById('billingDateFrom').value;
        const billingDateTo = document.getElementById('billingDateTo').value;
        if (billingDateFrom) {
            filters.push({
                field: "billing_month",
                type: ">=",
                value: billingDateFrom
            });
        }
        if (billingDateTo) {
            filters.push({
                field: "billing_month",
                type: "<=",
                value: billingDateTo
            });
        }

        // 仕掛検索
        const workInProgress = document.getElementById('searchWorkInProgress').value;
        if (workInProgress !== '') {
            filters.push({
                field: "work_in_progress",
                type: "=",
                value: workInProgress === 'true'
            });
        }

        // フィルターを適用
        this.table.setFilter(filters);
    }
}

// Initialize the OrderManager when the DOM is fully loaded
document.addEventListener('DOMContentLoaded', () => {
    window.orderManager = new OrderManager();
    // グローバル関数は不要になるので削除
    // function clearSearch() { orderManager.clearSearch(); }
    // function refreshOrders() { orderManager.refreshOrders(); }
});

