// Orders management JavaScript
class OrderManager {
    constructor() {
        this.currentPage = 1;
        this.perPage = 20;
        this.searchTerm = '';
        this.editingOrderId = null;
        this.deleteOrderId = null;
        
        this.initializeEventListeners();
        this.loadOrders();
    }
    
    initializeEventListeners() {
        // Search functionality
        const searchInput = document.getElementById('searchInput');
        let searchTimeout;
        
        searchInput.addEventListener('input', (e) => {
            clearTimeout(searchTimeout);
            searchTimeout = setTimeout(() => {
                this.searchTerm = e.target.value.trim();
                this.currentPage = 1;
                this.loadOrders();
            }, 500);
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
    
    async loadOrders() {
        try {
            this.showLoading();
            
            const params = new URLSearchParams({
                page: this.currentPage,
                per_page: this.perPage,
                search: this.searchTerm
            });
            
            const response = await fetch(`/api/orders?${params}`, {
                headers: {
                    'X-CSRFToken': document.querySelector('meta[name=csrf-token]').getAttribute('content')
                }
            });
            
            if (!response.ok) {
                throw new Error('データの取得に失敗しました');
            }
            
            const data = await response.json();
            this.renderOrders(data.orders);
            this.renderPagination(data);
            this.hideLoading();
            
        } catch (error) {
            console.error('Error loading orders:', error);
            this.showError('受注データの読み込み中にエラーが発生しました');
            this.hideLoading();
        }
    }
    
    renderOrders(orders) {
        const tbody = document.getElementById('ordersTableBody');
        const container = document.getElementById('ordersTableContainer');
        const emptyState = document.getElementById('emptyState');
        
        if (orders.length === 0) {
            container.style.display = 'none';
            emptyState.style.display = 'block';
            return;
        }
        
        container.style.display = 'block';
        emptyState.style.display = 'none';
        
        tbody.innerHTML = orders.map(order => `
            <tr>
                <td><strong>${this.escapeHtml(order.order_number)}</strong></td>
                <td>${this.escapeHtml(order.customer_name)}</td>
                <td>${this.escapeHtml(order.project_name)}</td>
                <td class="currency">¥${this.formatNumber(order.order_amount)}</td>
                <td>${this.formatDate(order.order_date)}</td>
                <td>${order.delivery_date ? this.formatDate(order.delivery_date) : '-'}</td>
                <td>
                    <span class="badge status-badge status-${order.status}">
                        ${this.escapeHtml(order.status)}
                    </span>
                </td>
                <td>
                    <button type="button" class="btn btn-sm btn-outline-primary btn-action" 
                            onclick="orderManager.editOrder(${order.id})" title="編集">
                        <i class="fas fa-edit"></i>
                    </button>
                    <button type="button" class="btn btn-sm btn-outline-danger btn-action" 
                            onclick="orderManager.confirmDelete(${order.id})" title="削除">
                        <i class="fas fa-trash"></i>
                    </button>
                </td>
            </tr>
        `).join('');
    }
    
    renderPagination(data) {
        const pagination = document.getElementById('pagination');
        
        if (data.pages <= 1) {
            pagination.innerHTML = '';
            return;
        }
        
        let paginationHtml = '';
        
        // Previous button
        if (data.page > 1) {
            paginationHtml += `
                <li class="page-item">
                    <a class="page-link" href="#" onclick="orderManager.goToPage(${data.page - 1})">
                        <i class="fas fa-chevron-left"></i>
                    </a>
                </li>
            `;
        }
        
        // Page numbers
        const startPage = Math.max(1, data.page - 2);
        const endPage = Math.min(data.pages, data.page + 2);
        
        for (let i = startPage; i <= endPage; i++) {
            paginationHtml += `
                <li class="page-item ${i === data.page ? 'active' : ''}">
                    <a class="page-link" href="#" onclick="orderManager.goToPage(${i})">${i}</a>
                </li>
            `;
        }
        
        // Next button
        if (data.page < data.pages) {
            paginationHtml += `
                <li class="page-item">
                    <a class="page-link" href="#" onclick="orderManager.goToPage(${data.page + 1})">
                        <i class="fas fa-chevron-right"></i>
                    </a>
                </li>
            `;
        }
        
        pagination.innerHTML = paginationHtml;
    }
    
    goToPage(page) {
        this.currentPage = page;
        this.loadOrders();
    }
    
    async editOrder(orderId) {
        try {
            // Get order data from the table (could also fetch from API)
            const orders = await this.fetchOrderData();
            const order = orders.find(o => o.id === orderId);
            
            if (!order) {
                this.showError('受注データが見つかりません');
                return;
            }
            
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
    
    async fetchOrderData() {
        const params = new URLSearchParams({
            page: this.currentPage,
            per_page: this.perPage,
            search: this.searchTerm
        });
        
        const response = await fetch(`/api/orders?${params}`, {
            headers: {
                'X-CSRFToken': document.querySelector('meta[name=csrf-token]').getAttribute('content')
            }
        });
        
        const data = await response.json();
        return data.orders;
    }
    
    populateForm(order) {
        document.getElementById('id').value = order.id;
        document.getElementById('order_number').value = order.order_number;
        document.getElementById('customer_name').value = order.customer_name;
        document.getElementById('project_name').value = order.project_name;
        document.getElementById('order_amount').value = order.order_amount;
        document.getElementById('order_date').value = order.order_date;
        document.getElementById('delivery_date').value = order.delivery_date || '';
        document.getElementById('status').value = order.status;
        document.getElementById('remarks').value = order.remarks || '';
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
            this.hideModal();
            this.loadOrders();
            
        } catch (error) {
            console.error('Error saving order:', error);
            this.showError(error.message || '保存中にエラーが発生しました');
        } finally {
            // Reset button state
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
            
            const data = await response.json();
            
            if (!response.ok) {
                throw new Error(data.error || '削除に失敗しました');
            }
            
            this.showSuccess(data.message);
            this.hideModal('deleteModal');
            this.loadOrders();
            
        } catch (error) {
            console.error('Error deleting order:', error);
            this.showError(error.message || '削除中にエラーが発生しました');
        }
    }
    
    resetForm() {
        document.getElementById('orderForm').reset();
        this.editingOrderId = null;
        this.clearValidationErrors();
        
        // Reset modal title
        document.getElementById('orderModalTitle').innerHTML = 
            '<i class="fas fa-plus me-2"></i>新規受注登録';
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
    
    showLoading() {
        document.getElementById('loadingSpinner').style.display = 'block';
        document.getElementById('ordersTableContainer').style.display = 'none';
        document.getElementById('emptyState').style.display = 'none';
    }
    
    hideLoading() {
        document.getElementById('loadingSpinner').style.display = 'none';
    }
    
    hideModal(modalId = 'orderModal') {
        const modal = bootstrap.Modal.getInstance(document.getElementById(modalId));
        if (modal) {
            modal.hide();
        }
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
    
    formatNumber(num) {
        return new Intl.NumberFormat('ja-JP').format(num);
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

// Global functions for onclick handlers
function clearSearch() {
    document.getElementById('searchInput').value = '';
    orderManager.searchTerm = '';
    orderManager.currentPage = 1;
    orderManager.loadOrders();
}

function refreshOrders() {
    orderManager.loadOrders();
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.orderManager = new OrderManager();
});
