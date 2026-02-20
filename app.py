"""
股票交易记录系统 - Stock Tracker
Flask 应用主文件
"""

from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
from functools import wraps
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///stock_tracker.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message = '请先登录以访问此页面'

# ==================== 数据库模型 ====================

class User(UserMixin, db.Model):
    """用户模型"""
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    trades = db.relationship('Trade', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    reflections = db.relationship('DailyReflection', backref='user', lazy='dynamic', cascade='all, delete-orphan')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Trade(db.Model):
    """交易记录模型"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    stock_code = db.Column(db.String(20), nullable=False)  # 股票代码
    stock_name = db.Column(db.String(100))  # 股票名称
    trade_type = db.Column(db.String(10), nullable=False)  # 'buy' 或 'sell'
    quantity = db.Column(db.Integer, nullable=False)  # 数量
    price = db.Column(db.Float, nullable=False)  # 价格
    amount = db.Column(db.Float)  # 总金额（自动计算）
    trade_date = db.Column(db.DateTime, nullable=False)  # 交易日期
    thought = db.Column(db.Text)  # 交易想法
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def calculate_amount(self):
        self.amount = self.quantity * self.price


class DailyReflection(db.Model):
    """每日复盘模型"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    reflection_date = db.Column(db.Date, nullable=False)  # 复盘日期
    content = db.Column(db.Text, nullable=False)  # 复盘内容
    profit_loss = db.Column(db.Float)  # 当日盈亏
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# ==================== 路由 ====================

@app.route('/')
def index():
    """首页"""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return render_template('index.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    """用户注册"""
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')

        if not username or not password:
            flash('用户名和密码不能为空', 'error')
            return render_template('register.html')

        if password != confirm_password:
            flash('两次输入的密码不一致', 'error')
            return render_template('register.html')

        if User.query.filter_by(username=username).first():
            flash('用户名已存在', 'error')
            return render_template('register.html')

        user = User(username=username)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()

        flash('注册成功，请登录', 'success')
        return redirect(url_for('login'))

    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    """用户登录"""
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        remember = request.form.get('remember', False)

        user = User.query.filter_by(username=username).first()

        if user and user.check_password(password):
            login_user(user, remember=remember)
            next_page = request.args.get('next')
            return redirect(next_page if next_page else url_for('dashboard'))

        flash('用户名或密码错误', 'error')

    return render_template('login.html')


@app.route('/logout')
@login_required
def logout():
    """用户登出"""
    logout_user()
    flash('已安全退出', 'success')
    return redirect(url_for('index'))


@app.route('/dashboard')
@login_required
def dashboard():
    """仪表盘"""
    # 获取最近 10 条交易记录
    recent_trades = Trade.query.filter_by(user_id=current_user.id)\
        .order_by(Trade.trade_date.desc()).limit(10).all()

    # 获取最近的复盘
    recent_reflections = DailyReflection.query.filter_by(user_id=current_user.id)\
        .order_by(DailyReflection.reflection_date.desc()).limit(5).all()

    # 统计信息
    total_trades = Trade.query.filter_by(user_id=current_user.id).count()
    total_reflections = DailyReflection.query.filter_by(user_id=current_user.id).count()

    return render_template('dashboard.html',
                         recent_trades=recent_trades,
                         recent_reflections=recent_reflections,
                         total_trades=total_trades,
                         total_reflections=total_reflections)


@app.route('/trades', methods=['GET', 'POST'])
@login_required
def trades():
    """交易记录管理"""
    if request.method == 'POST':
        stock_code = request.form.get('stock_code', '').strip()
        stock_name = request.form.get('stock_name', '').strip()
        trade_type = request.form.get('trade_type')
        quantity = request.form.get('quantity', type=int)
        price = request.form.get('price', type=float)
        trade_date_str = request.form.get('trade_date')
        thought = request.form.get('thought', '')

        if not all([stock_code, trade_type, quantity, price, trade_date_str]):
            flash('请填写必填字段', 'error')
            return redirect(url_for('trades'))

        trade_date = datetime.strptime(trade_date_str, '%Y-%m-%d')

        trade = Trade(
            user_id=current_user.id,
            stock_code=stock_code,
            stock_name=stock_name,
            trade_type=trade_type,
            quantity=quantity,
            price=price,
            trade_date=trade_date,
            thought=thought
        )
        trade.calculate_amount()

        db.session.add(trade)
        db.session.commit()

        flash('交易记录添加成功', 'success')
        return redirect(url_for('trades'))

    # 获取所有交易记录
    page = request.args.get('page', 1, type=int)
    trades_query = Trade.query.filter_by(user_id=current_user.id)\
        .order_by(Trade.trade_date.desc())

    trades_paginated = trades_query.paginate(page=page, per_page=20, error_out=False)

    return render_template('trades.html', trades=trades_paginated)


@app.route('/trades/delete/<int:id>')
@login_required
def delete_trade(id):
    """删除交易记录"""
    trade = Trade.query.filter_by(id=id, user_id=current_user.id).first_or_404()
    db.session.delete(trade)
    db.session.commit()
    flash('交易记录已删除', 'success')
    return redirect(url_for('trades'))


@app.route('/reflections', methods=['GET', 'POST'])
@login_required
def reflections():
    """每日复盘管理"""
    if request.method == 'POST':
        reflection_date_str = request.form.get('reflection_date')
        content = request.form.get('content', '').strip()
        profit_loss = request.form.get('profit_loss', type=float)

        if not all([reflection_date_str, content]):
            flash('请填写必填字段', 'error')
            return redirect(url_for('reflections'))

        reflection_date = datetime.strptime(reflection_date_str, '%Y-%m-%d').date()

        # 检查是否已存在该日期的复盘
        existing = DailyReflection.query.filter_by(
            user_id=current_user.id,
            reflection_date=reflection_date
        ).first()

        if existing:
            flash('该日期已有复盘记录，将进行更新', 'warning')
            existing.content = content
            existing.profit_loss = profit_loss
        else:
            reflection = DailyReflection(
                user_id=current_user.id,
                reflection_date=reflection_date,
                content=content,
                profit_loss=profit_loss
            )
            db.session.add(reflection)

        db.session.commit()
        flash('复盘记录保存成功', 'success')
        return redirect(url_for('reflections'))

    # 获取所有复盘记录
    page = request.args.get('page', 1, type=int)
    reflections_query = DailyReflection.query.filter_by(user_id=current_user.id)\
        .order_by(DailyReflection.reflection_date.desc())

    reflections_paginated = reflections_query.paginate(page=page, per_page=20, error_out=False)

    return render_template('reflections.html', reflections=reflections_paginated)


@app.route('/reflections/delete/<int:id>')
@login_required
def delete_reflection(id):
    """删除复盘记录"""
    reflection = DailyReflection.query.filter_by(id=id, user_id=current_user.id).first_or_404()
    db.session.delete(reflection)
    db.session.commit()
    flash('复盘记录已删除', 'success')
    return redirect(url_for('reflections'))


@app.route('/reports')
@login_required
def reports():
    """报表页面"""
    report_type = request.args.get('type', 'daily')  # daily, monthly, yearly
    year = request.args.get('year', datetime.now().year, type=int)
    month = request.args.get('month', datetime.now().month, type=int)
    day = request.args.get('day', datetime.now().day, type=int)

    trades_query = Trade.query.filter_by(user_id=current_user.id)

    if report_type == 'daily':
        target_date = datetime(year, month, day).date()
        trades = trades_query.filter(
            db.func.date(Trade.trade_date) == target_date
        ).order_by(Trade.trade_date.desc()).all()

        # 计算当日统计
        buy_amount = sum(t.amount for t in trades if t.trade_type == 'buy')
        sell_amount = sum(t.amount for t in trades if t.trade_type == 'sell')

        report_data = {
            'date': target_date,
            'total_trades': len(trades),
            'buy_count': sum(1 for t in trades if t.trade_type == 'buy'),
            'sell_count': sum(1 for t in trades if t.trade_type == 'sell'),
            'buy_amount': buy_amount,
            'sell_amount': sell_amount,
            'net_amount': sell_amount - buy_amount
        }

    elif report_type == 'monthly':
        trades = trades_query.filter(
            db.extract('year', Trade.trade_date) == year,
            db.extract('month', Trade.trade_date) == month
        ).order_by(Trade.trade_date.desc()).all()

        # 按日期分组统计
        daily_stats = {}
        for t in trades:
            date_key = t.trade_date.strftime('%Y-%m-%d')
            if date_key not in daily_stats:
                daily_stats[date_key] = {'buy': 0, 'sell': 0, 'buy_amount': 0, 'sell_amount': 0}
            if t.trade_type == 'buy':
                daily_stats[date_key]['buy'] += 1
                daily_stats[date_key]['buy_amount'] += t.amount
            else:
                daily_stats[date_key]['sell'] += 1
                daily_stats[date_key]['sell_amount'] += t.amount

        report_data = {
            'year': year,
            'month': month,
            'total_trades': len(trades),
            'daily_stats': daily_stats
        }

    else:  # yearly
        trades = trades_query.filter(
            db.extract('year', Trade.trade_date) == year
        ).order_by(Trade.trade_date.desc()).all()

        # 按月份分组统计
        monthly_stats = {}
        for t in trades:
            month_key = t.trade_date.strftime('%Y-%m')
            if month_key not in monthly_stats:
                monthly_stats[month_key] = {'buy': 0, 'sell': 0, 'buy_amount': 0, 'sell_amount': 0}
            if t.trade_type == 'buy':
                monthly_stats[month_key]['buy'] += 1
                monthly_stats[month_key]['buy_amount'] += t.amount
            else:
                monthly_stats[month_key]['sell'] += 1
                monthly_stats[month_key]['sell_amount'] += t.amount

        report_data = {
            'year': year,
            'total_trades': len(trades),
            'monthly_stats': monthly_stats
        }

    return render_template('reports.html',
                         report_type=report_type,
                         report_data=report_data,
                         trades=trades,
                         current_year=year,
                         current_month=month,
                         current_day=day)


@app.route('/api/trades/<int:id>', methods=['PUT'])
@login_required
def update_trade(id):
    """更新交易记录（API）"""
    trade = Trade.query.filter_by(id=id, user_id=current_user.id).first_or_404()

    data = request.get_json()
    if data:
        if 'thought' in data:
            trade.thought = data['thought']
        if 'stock_name' in data:
            trade.stock_name = data['stock_name']

    db.session.commit()
    return jsonify({'success': True})


# ==================== 错误处理 ====================

@app.errorhandler(404)
def not_found(error):
    return render_template('error.html', error='页面未找到'), 404


@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('error.html', error='服务器内部错误'), 500


# ==================== 初始化数据库 ====================

def init_db():
    """初始化数据库"""
    with app.app_context():
        db.create_all()
        print('数据库初始化完成')


if __name__ == '__main__':
    init_db()
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
