from flask import render_template, request, redirect, url_for, flash, jsonify, session
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import check_password_hash
from sqlalchemy import and_, or_, func, distinct
from decimal import Decimal
import logging
from datetime import datetime, timedelta, date
from calendar import monthrange

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
    if current_user.is_authenticated:
        return redirect(url_for('orders'))
    
    form = RegisterForm()
    if form.validate_on_submit():
        try:
            user = User(
                username=form.username.data,
                email=form.email.data
            )
            user.set_password(form.password.data)
            
            db.session.add(user)
            db.session.commit()
            
            flash('アカウントが作成されました。ログインしてください。', 'success')
            logging.info(f"New user registered: {user.username}")
            return redirect(url_for('login'))
        
        except Exception as e:
            db.session.rollback()
            flash('アカウント作成中にエラーが発生しました', 'error')
            logging.error(f"Error creating user: {e}")
    
    return render_template('register.html', form=form)

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
        query = Order.query.filter_by(user_id=current_user.id)
        
        if search:
            search_filter = or_(
                Order.order_number.contains(search),
                Order.customer_name.contains(search),
                Order.project_name.contains(search),
                Order.status.contains(search)
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
            # Check if order number already exists for this user
            existing_order = Order.query.filter_by(
                user_id=current_user.id,
                order_number=form.order_number.data
            ).first()
            
            if existing_order:
                return jsonify({'error': 'この受注番号は既に存在します'}), 400
            
            order = Order(
                user_id=current_user.id,
                order_number=form.order_number.data,
                customer_name=form.customer_name.data,
                project_name=form.project_name.data,
                order_amount=form.order_amount.data,
                order_date=form.order_date.data,
                delivery_date=form.delivery_date.data,
                status=form.status.data,
                remarks=form.remarks.data
            )
            
            db.session.add(order)
            db.session.commit()
            
            logging.info(f"Order created: {order.order_number} by user {current_user.username}")
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
    order = Order.query.filter_by(id=order_id, user_id=current_user.id).first_or_404()
    
    form = OrderForm()
    if form.validate_on_submit():
        try:
            # Check if order number already exists for this user (excluding current order)
            existing_order = Order.query.filter(
                and_(
                    Order.user_id == current_user.id,
                    Order.order_number == form.order_number.data,
                    Order.id != order_id
                )
            ).first()
            
            if existing_order:
                return jsonify({'error': 'この受注番号は既に存在します'}), 400
            
            # Update order fields
            order.order_number = form.order_number.data
            order.customer_name = form.customer_name.data
            order.project_name = form.project_name.data
            order.order_amount = form.order_amount.data
            order.order_date = form.order_date.data
            order.delivery_date = form.delivery_date.data
            order.status = form.status.data
            order.remarks = form.remarks.data
            
            db.session.commit()
            
            logging.info(f"Order updated: {order.order_number} by user {current_user.username}")
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
    order = Order.query.filter_by(id=order_id, user_id=current_user.id).first_or_404()
    
    try:
        db.session.delete(order)
        db.session.commit()
        
        logging.info(f"Order deleted: {order.order_number} by user {current_user.username}")
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
            .filter_by(user_id=current_user.id)\
            .order_by(Order.project_name)\
            .all()
        
        return jsonify({
            'projects': [project[0] for project in projects]
        })
    
    except Exception as e:
        logging.error(f"Error fetching projects: {e}")
        return jsonify({'error': 'プロジェクト一覧の取得中にエラーが発生しました'}), 500

@app.route('/api/orders/period', methods=['GET'])
@login_required
@limiter.limit("60 per minute")
def api_get_orders_by_period():
    try:
        project_name = request.args.get('project')
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        if not all([project_name, start_date, end_date]):
            return jsonify({'error': 'プロジェクト名と期間を指定してください'}), 400
        
        # 日付文字列をdatetimeオブジェクトに変換
        try:
            # YYYY-MM形式をYYYY-MM-DD形式に変換
            start_year, start_month = map(int, start_date.split('-'))
            start_date_obj = date(start_year, start_month, 1)
            
            end_year, end_month = map(int, end_date.split('-'))
            _, last_day = monthrange(end_year, end_month)
            end_date_obj = date(end_year, end_month, last_day)
        except ValueError:
            return jsonify({'error': '無効な年月形式です'}), 400
        
        # 指定された期間とプロジェクトの受注を取得
        query = Order.query.filter(
            Order.user_id == current_user.id,
            Order.order_date >= start_date_obj,
            Order.order_date <= end_date_obj
        )

        if project_name != 'all':
            query = query.filter(Order.project_name == project_name)

        orders = query.all()
        
        # 総売上を計算
        total_revenue = sum(order.order_amount for order in orders)
        
        return jsonify({
            'orders': [order.to_dict() for order in orders],
            'total_revenue': float(total_revenue),
            'start_date': start_date_obj.strftime('%Y-%m'),
            'end_date': end_date_obj.strftime('%Y-%m'),
            'project_name': project_name
        })
    
    except ValueError as e:
        logging.error(f"Invalid date format or data for orders by period: {e}")
        return jsonify({'error': '日付の形式が正しくありません'}), 400
    except Exception as e:
        logging.error(f"Error fetching orders by period: {e}")
        return jsonify({'error': 'データの取得中にエラーが発生しました'}), 500

@app.route('/api/profit-data', methods=['GET'])
@login_required
@limiter.limit("60 per minute")
def api_get_profit_data():
    try:
        project = request.args.get('project')
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        # コストの取得とバリデーション
        try:
            employee_cost = int(request.args.get('employee_cost', 0))
            bp_cost = int(request.args.get('bp_cost', 0))
            if employee_cost < 0 or bp_cost < 0:
                return jsonify({'error': 'コストは0以上の整数で入力してください'}), 400
        except ValueError:
            return jsonify({'error': 'コストは整数で入力してください'}), 400
        
        if not all([project, start_date, end_date]):
            return jsonify({'error': 'プロジェクトと期間を指定してください'}), 400
            
        # 日付のバリデーションと変換
        try:
            # YYYY-MM形式をYYYY-MM-DD形式に変換
            start_year, start_month = map(int, start_date.split('-'))
            start_date_obj = date(start_year, start_month, 1)
            
            end_year, end_month = map(int, end_date.split('-'))
            _, last_day = monthrange(end_year, end_month)
            end_date_obj = date(end_year, end_month, last_day)
        except ValueError:
            return jsonify({'error': '無効な年月形式です'}), 400
            
        # 期間内の受注を取得
        query = Order.query.filter(
            Order.user_id == current_user.id,
            Order.order_date >= start_date_obj,
            Order.order_date <= end_date_obj
        )

        if project != 'all':
            query = query.filter(Order.project_name == project)

        orders = query.all()
        
        # 売上合計を計算
        total_revenue = sum(order.order_amount for order in orders)
        
        # コストを加味した利益計算
        total_cost = employee_cost + bp_cost
        profit = total_revenue - total_cost
        
        # 利益率の計算（確実に数値型として計算）
        profit_rate = float(0)
        if total_revenue > 0:
            profit_rate = float(profit) / float(total_revenue) * 100
        
        return jsonify({
            'project_name': project,
            'start_date': start_date_obj.strftime('%Y-%m'),
            'end_date': end_date_obj.strftime('%Y-%m'),
            'total_revenue': float(total_revenue),
            'total_cost': float(total_cost),
            'profit': float(profit),
            'profit_rate': float(profit_rate),
            'employee_cost': float(employee_cost),
            'bp_cost': float(bp_cost)
        })
    
    except Exception as e:
        logging.error(f"Error fetching profit data: {e}")
        return jsonify({'error': '利益データの取得中にエラーが発生しました'}), 500

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
