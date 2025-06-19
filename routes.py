from flask import render_template, request, redirect, url_for, flash, jsonify, session, Blueprint, current_app
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import check_password_hash
from sqlalchemy import and_, or_, func, distinct
from decimal import Decimal
import logging
from datetime import datetime, timedelta, date
from functools import wraps
import functools
from urllib.parse import urlparse

from app import limiter
from models import User, Order
from forms import LoginForm, OrderForm, UserForm

main_bp = Blueprint('main', __name__)

# 定数を定義
ADMIN_USERS_ROUTE = 'main.admin_users'

@main_bp.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('main.orders'))
    return redirect(url_for('main.login'))

@main_bp.route('/login', methods=['GET', 'POST'])
@limiter.limit("5 per minute")
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = current_app.extensions['sqlalchemy'].session.query(User).filter_by(username=form.username.data).first()
        
        if user and user.check_password(form.password.data) and user.is_active:
            login_user(user, remember=True)
            next_page = request.args.get('next')
            flash('ログインしました', 'success')
            # URLリダイレクトの脆弱性を防ぐためのロジックを修正
            if next_page and urlparse(next_page).netloc == '': # next_pageが存在し、かつ外部URLでない場合
                return redirect(next_page)
            return redirect(url_for('main.orders')) # 外部URLまたはnext_pageがない場合はデフォルトページにリダイレクト
        else:
            flash('ユーザー名またはパスワードが正しくありません', 'error')
            logging.warning(f"Failed login attempt for username: {form.username.data}")
    
    return render_template('login.html', form=form)

@main_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('ログアウトしました', 'info')
    return redirect(url_for('main.login'))

@main_bp.route('/orders')
@login_required
def orders():
    form = OrderForm()
    return render_template('orders.html', form=form)

@main_bp.route('/api/orders', methods=['GET'])
@login_required
@limiter.limit("60 per minute")
def api_get_orders():
    try:
        # Get pagination parameters
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 50, type=int), 100)  # Limit max per_page
        
        # Get search parameters
        search = request.args.get('search', '').strip()
        
        # Build query
        query = current_app.extensions['sqlalchemy'].session.query(Order)
        
        if search:
            search_filter = or_(
                Order.customer_name.contains(search),
                Order.project_name.contains(search)
            )
            query = query.filter(search_filter)
        
        # Get total count
        total = query.count()
        
        # Apply pagination and ordering
        orders = query.order_by(Order.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        return jsonify({
            'orders': [order.to_dict() for order in orders.items],
            'total': total,
            'page': page,
            'per_page': per_page,
            'pages': orders.pages
        })
    
    except Exception as e:
        logging.error(f"Error fetching orders: {e}")
        return jsonify({'error': 'データの取得中にエラーが発生しました'}), 500

@main_bp.route('/api/orders', methods=['POST'])
@login_required
@limiter.limit("30 per minute")
def api_create_order():
    form = OrderForm()
    if form.validate_on_submit():
        try:
            order = Order(
                customer_name=form.customer_name.data,
                project_name=form.project_name.data,
                sales_amount=form.sales_amount.data,
                order_amount=form.order_amount.data,
                invoiced_amount=form.invoiced_amount.data,
                order_date=form.order_date.data,
                contract_type=form.contract_type.data,
                sales_stage=form.sales_stage.data,
                billing_month=form.billing_month.data,
                work_in_progress=form.work_in_progress.data,
                description=form.description.data
            )
            
            current_app.extensions['sqlalchemy'].session.add(order)
            current_app.extensions['sqlalchemy'].session.commit()
            
            logging.info(f"Order created for project: {order.project_name}")
            return jsonify({'message': '受注が登録されました', 'order': order.to_dict()}), 201
        
        except Exception as e:
            current_app.extensions['sqlalchemy'].session.rollback()
            logging.error(f"Error creating order: {e}")
            return jsonify({'error': '受注登録中にエラーが発生しました'}), 500
    
    return jsonify({'error': 'バリデーションエラー', 'errors': form.errors}), 400

@main_bp.route('/api/orders/<int:order_id>', methods=['PUT'])
@login_required
@limiter.limit("30 per minute")
def api_update_order(order_id):
    db = current_app.extensions['sqlalchemy']
    order = db.session.query(Order).get_or_404(order_id)
    
    form = OrderForm()
    if form.validate_on_submit():
        try:
            # Update order fields
            order.customer_name = form.customer_name.data
            order.project_name = form.project_name.data
            order.sales_amount = form.sales_amount.data
            order.order_amount = form.order_amount.data
            order.invoiced_amount = form.invoiced_amount.data
            order.order_date = form.order_date.data
            order.contract_type = form.contract_type.data
            order.sales_stage = form.sales_stage.data
            order.billing_month = form.billing_month.data
            order.work_in_progress = form.work_in_progress.data
            order.description = form.description.data
            
            db.session.commit()
            
            logging.info(f"Order updated: {order.project_name}")
            return jsonify({'message': '受注が更新されました', 'order': order.to_dict()})
        
        except Exception as e:
            db.session.rollback()
            logging.error(f"Error updating order: {e}")
            return jsonify({'error': '受注更新中にエラーが発生しました'}), 500
    
    return jsonify({'error': 'バリデーションエラー', 'errors': form.errors}), 400

@main_bp.route('/api/orders/<int:order_id>', methods=['DELETE'])
@login_required
@limiter.limit("20 per minute")
def api_delete_order(order_id):
    db = current_app.extensions['sqlalchemy']
    order = db.session.query(Order).get_or_404(order_id)
    
    try:
        db.session.delete(order)
        db.session.commit()
        
        logging.info(f"Order deleted for project: {order.project_name}")
        return jsonify({'message': '受注が削除されました'})
    
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error deleting order: {e}")
        return jsonify({'error': '受注削除中にエラーが発生しました'}), 500

@main_bp.route('/profit-analysis')
@login_required
def profit_analysis():
    return render_template('profit_analysis.html')

@main_bp.route('/api/projects', methods=['GET'])
@login_required
@limiter.limit("60 per minute")
def api_get_projects():
    try:
        # プロジェクト名の一覧を取得（重複を除く）
        projects = current_app.extensions['sqlalchemy'].session.query(distinct(Order.project_name))\
            .order_by(Order.project_name)\
            .all()
        
        return jsonify({
            'projects': [project[0] for project in projects]
        })
    
    except Exception as e:
        logging.error(f"Error fetching projects: {e}")
        return jsonify({'error': 'プロジェクトの取得中にエラーが発生しました'}), 500

@main_bp.route('/api/profit-data', methods=['GET'])
@login_required
@limiter.limit("60 per minute")
def api_get_profit_data():
    project_name = request.args.get('project_name')
    start_date_str = request.args.get('start_date')
    end_date_str = request.args.get('end_date')

    try:
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()

        # クエリの構築
        query = current_app.extensions['sqlalchemy'].session.query(Order).filter(Order.order_date.between(start_date, end_date))
        
        # プロジェクト名が'all'でない場合は、特定のプロジェクトでフィルタリング
        if project_name != 'all':
            query = query.filter(Order.project_name == project_name)

        # 受注データを取得
        orders = query.all()

        total_sales_amount = sum(float(order.sales_amount) for order in orders)
        total_order_amount = sum(float(order.order_amount) for order in orders)
        total_invoiced_amount = sum(float(order.invoiced_amount) for order in orders)

        return jsonify({
            'total_sales_amount': total_sales_amount,
            'total_order_amount': total_order_amount,
            'total_invoiced_amount': total_invoiced_amount
        })

    except ValueError:
        flash('日付の形式が正しくありません。YYYY-MM-DD形式を使用してください。', 'error')
        return jsonify({'error': '日付の形式が正しくありません。YYYY-MM-DD形式を使用してください。'}), 400
    except Exception as e:
        logging.error(f"Error calculating profit data: {e}")
        flash('利益データの計算中にエラーが発生しました', 'error')
        return jsonify({'error': '利益データの計算中にエラーが発生しました'}), 500

@main_bp.route('/user/delete', methods=['POST'])
@login_required
@limiter.limit("5 per minute")
def delete_user():
    user_id = request.json.get('id')
    if not user_id:
        return jsonify({'error': 'ユーザーIDが指定されていません'}), 400

    db = current_app.extensions['sqlalchemy']
    user_to_delete = db.session.query(User).get(user_id)

    if user_to_delete:
        try:
            db.session.delete(user_to_delete)
            db.session.commit()
            return jsonify({'message': 'ユーザーが削除されました'}), 200
        except Exception as e:
            db.session.rollback()
            logging.error(f"Error deleting user: {e}")
            return jsonify({'error': 'ユーザー削除中にエラーが発生しました'}), 500
    else:
        return jsonify({'error': '指定されたユーザーが見つかりません'}), 404

@main_bp.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404

@main_bp.errorhandler(500)
def internal_error(error):
    return render_template('500.html'), 500

@main_bp.errorhandler(429)
def ratelimit_handler(e):
    return render_template('429.html'), 429

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_admin:
            flash('管理者権限が必要です。', 'error')
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    return decorated_function

@main_bp.route('/admin/users')
@login_required
@admin_required
def admin_users():
    users = current_app.extensions['sqlalchemy'].session.query(User).all()
    return render_template('admin/users.html', users=users)

@main_bp.route('/admin/users/create', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_create_user():
    form = LoginForm() # Reuse LoginForm for user creation
    if form.validate_on_submit():
        db = current_app.extensions['sqlalchemy']
        username = form.username.data
        password = form.password.data
        email = request.form.get('email')
        is_admin = bool(request.form.get('is_admin'))

        existing_user = db.session.query(User).filter_by(username=username).first()
        existing_email = db.session.query(User).filter_by(email=email).first()

        if existing_user:
            flash('ユーザー名は既に存在します。', 'error')
        elif existing_email:
            flash('メールアドレスは既に存在します。', 'error')
        else:
            new_user = User(username=username, email=email, is_admin=is_admin)
            new_user.set_password(password)
            db.session.add(new_user)
            db.session.commit()
            flash('ユーザーが正常に作成されました。', 'success')
            return redirect(url_for(ADMIN_USERS_ROUTE))
    return render_template('admin/create_user.html', form=form)

@main_bp.route('/admin/users/<int:user_id>/delete', methods=['POST'])
@login_required
@admin_required
def admin_delete_user(user_id):
    db = current_app.extensions['sqlalchemy']
    user_to_delete = db.session.query(User).get_or_404(user_id)
    try:
        db.session.delete(user_to_delete)
        db.session.commit()
        flash('ユーザーが削除されました。', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'ユーザー削除中にエラーが発生しました: {e}', 'error')
        logging.error(f"Error deleting user {user_id}: {e}")
    return redirect(url_for(ADMIN_USERS_ROUTE))

@main_bp.route('/admin/users/<int:user_id>/toggle-admin', methods=['POST'])
@login_required
@admin_required
def admin_toggle_admin(user_id):
    db = current_app.extensions['sqlalchemy']
    user = db.session.query(User).get_or_404(user_id)
    try:
        user.is_admin = not user.is_admin
        db.session.commit()
        flash(f'{user.username} の管理者権限がトグルされました。', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'管理者権限のトグル中にエラーが発生しました: {e}', 'error')
        logging.error(f"Error toggling admin status for user {user_id}: {e}")
    return redirect(url_for(ADMIN_USERS_ROUTE))
