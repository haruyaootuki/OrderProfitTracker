from flask import render_template, request, redirect, url_for, flash, jsonify, session
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import check_password_hash
from sqlalchemy import and_, or_, func, distinct
from decimal import Decimal
import logging
from datetime import datetime, timedelta, date
from calendar import monthrange
from functools import wraps

from app import app, db, limiter
from models import User, Order
from forms import LoginForm, RegisterForm, OrderForm

@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('orders'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
@limiter.limit("5 per minute")
def login():
    if current_user.is_authenticated:
        return redirect(url_for('orders'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        
        if user and user.check_password(form.password.data) and user.is_active:
            login_user(user, remember=True)
            next_page = request.args.get('next')
            flash('ログインしました', 'success')
            return redirect(next_page) if next_page else redirect(url_for('orders'))
        else:
            flash('ユーザー名またはパスワードが正しくありません', 'error')
            logging.warning(f"Failed login attempt for username: {form.username.data}")
    
    return render_template('login.html', form=form)

@app.route('/register', methods=['GET', 'POST'])
@limiter.limit("3 per minute")
def register():
    # 一般ユーザーの登録を無効化
    flash('現在、新規ユーザー登録は受け付けていません。管理者にお問い合わせください。', 'info')
    return redirect(url_for('login'))

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('ログアウトしました', 'info')
    return redirect(url_for('login'))

@app.route('/orders')
@login_required
def orders():
    form = OrderForm()
    return render_template('orders.html', form=form)

@app.route('/api/orders', methods=['GET'])
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
        query = Order.query
        
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

@app.route('/api/orders', methods=['POST'])
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
            
            db.session.add(order)
            db.session.commit()
            
            logging.info(f"Order created for project: {order.project_name}")
            return jsonify({'message': '受注が登録されました', 'order': order.to_dict()}), 201
        
        except Exception as e:
            db.session.rollback()
            logging.error(f"Error creating order: {e}")
            return jsonify({'error': '受注登録中にエラーが発生しました'}), 500
    
    return jsonify({'error': 'バリデーションエラー', 'errors': form.errors}), 400

@app.route('/api/orders/<int:order_id>', methods=['PUT'])
@login_required
@limiter.limit("30 per minute")
def api_update_order(order_id):
    order = Order.query.get_or_404(order_id)
    
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

@app.route('/api/orders/<int:order_id>', methods=['DELETE'])
@login_required
@limiter.limit("20 per minute")
def api_delete_order(order_id):
    order = Order.query.get_or_404(order_id)
    
    try:
        db.session.delete(order)
        db.session.commit()
        
        logging.info(f"Order deleted for project: {order.project_name}")
        return jsonify({'message': '受注が削除されました'})
    
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error deleting order: {e}")
        return jsonify({'error': '受注削除中にエラーが発生しました'}), 500

@app.route('/profit-analysis')
@login_required
def profit_analysis():
    return render_template('profit_analysis.html')

@app.route('/api/projects', methods=['GET'])
@login_required
@limiter.limit("60 per minute")
def api_get_projects():
    try:
        # プロジェクト名の一覧を取得（重複を除く）
        projects = db.session.query(distinct(Order.project_name))\
            .order_by(Order.project_name)\
            .all()
        
        return jsonify({
            'projects': [project[0] for project in projects]
        })
    
    except Exception as e:
        logging.error(f"Error fetching projects: {e}")
        return jsonify({'error': 'プロジェクトの取得中にエラーが発生しました'}), 500

@app.route('/api/profit-data', methods=['GET'])
@login_required
@limiter.limit("60 per minute")
def api_get_profit_data():
    project_name = request.args.get('project_name')
    start_date_str = request.args.get('start_date')
    end_date_str = request.args.get('end_date')

    if not all([project_name, start_date_str, end_date_str]):
        return jsonify({'error': 'プロジェクト名、開始日、終了日は必須です'}), 400

    try:
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()

        # クエリの構築
        query = Order.query.filter(Order.order_date.between(start_date, end_date))
        
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
        return jsonify({'error': '日付の形式が正しくありません。YYYY-MM-DD形式を使用してください。'}), 400
    except Exception as e:
        logging.error(f"Error calculating profit data: {e}")
        return jsonify({'error': '利益データの計算中にエラーが発生しました'}), 500

@app.route('/user/delete', methods=['POST'])
@login_required
@limiter.limit("5 per minute")
def delete_user():
    try:
        # ユーザーに関連するデータを削除（必要な場合）
        # 例: Order.query.filter_by(user_id=current_user.id).delete()
        
        # ユーザーを削除
        db.session.delete(current_user)
        db.session.commit()
        
        # ログアウト
        logout_user()
        
        flash('アカウントが削除されました', 'success')
        logging.info(f"User account deleted: {current_user.username}")
        return redirect(url_for('login'))
    
    except Exception as e:
        db.session.rollback()
        flash('アカウント削除中にエラーが発生しました', 'error')
        logging.error(f"Error deleting user account: {e}")
        return redirect(url_for('orders'))

@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('500.html'), 500

@app.errorhandler(429)
def ratelimit_handler(e):
    return jsonify({'error': 'アクセス制限に達しました。しばらく待ってからやり直してください。'}), 429

# 管理者権限チェック用デコレータ
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            flash('管理者権限が必要です', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/admin/users')
@login_required
@admin_required
def admin_users():
    users = User.query.order_by(User.created_at.desc()).all()
    return render_template('admin/users.html', users=users)

@app.route('/admin/users/create', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_create_user():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        email = request.form.get('email')
        is_admin = request.form.get('is_admin') == 'true'
        
        if not all([username, password, email]):
            flash('ユーザー名、メールアドレス、パスワードは必須です', 'error')
            return redirect(url_for('admin_create_user'))
        
        if User.query.filter_by(username=username).first():
            flash('このユーザー名は既に使用されています', 'error')
            return redirect(url_for('admin_create_user'))
        
        if User.query.filter_by(email=email).first():
            flash('このメールアドレスは既に使用されています', 'error')
            return redirect(url_for('admin_create_user'))
        
        try:
            user = User(username=username, email=email, is_admin=is_admin)
            user.set_password(password)
            db.session.add(user)
            db.session.commit()
            flash('ユーザーを作成しました', 'success')
            return redirect(url_for('admin_users'))
        except Exception as e:
            db.session.rollback()
            logging.error(f"Error creating user: {e}")
            flash('ユーザー作成中にエラーが発生しました', 'error')
            return redirect(url_for('admin_create_user'))
    
    return render_template('admin/create_user.html')

@app.route('/admin/users/<int:user_id>/delete', methods=['POST'])
@login_required
@admin_required
def admin_delete_user(user_id):
    if user_id == current_user.id:
        flash('自分自身のアカウントは削除できません', 'error')
        return redirect(url_for('admin_users'))
    
    user = User.query.get_or_404(user_id)
    try:
        db.session.delete(user)
        db.session.commit()
        flash('ユーザーを削除しました', 'success')
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error deleting user: {e}")
        flash('ユーザー削除中にエラーが発生しました', 'error')
    
    return redirect(url_for('admin_users'))

@app.route('/admin/users/<int:user_id>/toggle-admin', methods=['POST'])
@login_required
@admin_required
def admin_toggle_admin(user_id):
    if user_id == current_user.id:
        flash('自分自身の管理者権限は変更できません', 'error')
        return redirect(url_for('admin_users'))
    
    user = User.query.get_or_404(user_id)
    try:
        user.is_admin = not user.is_admin
        db.session.commit()
        status = '付与' if user.is_admin else '削除'
        flash(f'管理者権限を{status}しました', 'success')
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error toggling admin status: {e}")
        flash('権限変更中にエラーが発生しました', 'error')
    
    return redirect(url_for('admin_users'))
