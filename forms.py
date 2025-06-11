from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, DecimalField, DateField, TextAreaField, SelectField, HiddenField
from wtforms.validators import DataRequired, Email, Length, NumberRange, Optional, ValidationError
from wtforms.widgets import NumberInput
from models import User
import re

class LoginForm(FlaskForm):
    username = StringField('ユーザー名', validators=[
        DataRequired(message='ユーザー名は必須です'),
        Length(min=3, max=64, message='ユーザー名は3文字以上64文字以下で入力してください')
    ])
    password = PasswordField('パスワード', validators=[
        DataRequired(message='パスワードは必須です')
    ])

class RegisterForm(FlaskForm):
    username = StringField('ユーザー名', validators=[
        DataRequired(message='ユーザー名は必須です'),
        Length(min=3, max=64, message='ユーザー名は3文字以上64文字以下で入力してください')
    ])
    email = StringField('メールアドレス', validators=[
        DataRequired(message='メールアドレスは必須です'),
        Email(message='正しいメールアドレスを入力してください'),
        Length(max=120, message='メールアドレスは120文字以下で入力してください')
    ])
    password = PasswordField('パスワード', validators=[
        DataRequired(message='パスワードは必須です'),
        Length(min=8, message='パスワードは8文字以上で入力してください')
    ])
    
    def validate_username(self, username):
        # Check for valid characters (alphanumeric and underscore only)
        if not re.match(r'^[a-zA-Z0-9_]+$', username.data):
            raise ValidationError('ユーザー名は英数字とアンダースコアのみ使用できます')
        
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('このユーザー名は既に使用されています')
    
    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('このメールアドレスは既に使用されています')

class OrderForm(FlaskForm):
    id = HiddenField()
    order_number = StringField('受注番号', validators=[
        DataRequired(message='受注番号は必須です'),
        Length(max=100, message='受注番号は100文字以下で入力してください')
    ])
    customer_name = StringField('顧客名', validators=[
        DataRequired(message='顧客名は必須です'),
        Length(max=200, message='顧客名は200文字以下で入力してください')
    ])
    project_name = StringField('プロジェクト名', validators=[
        DataRequired(message='プロジェクト名は必須です'),
        Length(max=200, message='プロジェクト名は200文字以下で入力してください')
    ])
    order_amount = DecimalField('受注金額', validators=[
        DataRequired(message='受注金額は必須です'),
        NumberRange(min=0, message='受注金額は0以上で入力してください')
    ], widget=NumberInput(step='0.01'))
    order_date = DateField('受注日', validators=[
        DataRequired(message='受注日は必須です')
    ])
    delivery_date = DateField('納期', validators=[
        Optional()
    ])
    status = SelectField('ステータス', choices=[
        ('受注', '受注'),
        ('進行中', '進行中'),
        ('完了', '完了'),
        ('キャンセル', 'キャンセル')
    ], validators=[DataRequired(message='ステータスは必須です')])
    remarks = TextAreaField('備考', validators=[
        Optional(),
        Length(max=1000, message='備考は1000文字以下で入力してください')
    ])

class CostForm(FlaskForm):
    employee_cost = DecimalField('社員原価', validators=[
        DataRequired(message='社員原価は必須です'),
        NumberRange(min=0, message='社員原価は0以上で入力してください')
    ], widget=NumberInput(step='0.01'))
    bp_cost = DecimalField('BP原価', validators=[
        DataRequired(message='BP原価は必須です'),
        NumberRange(min=0, message='BP原価は0以上で入力してください')
    ], widget=NumberInput(step='0.01'))
    period_start = DateField('期間開始日', validators=[
        DataRequired(message='期間開始日は必須です')
    ])
    period_end = DateField('期間終了日', validators=[
        DataRequired(message='期間終了日は必須です')
    ])
    
    def validate_period_end(self, period_end):
        if self.period_start.data and period_end.data:
            if period_end.data <= self.period_start.data:
                raise ValidationError('期間終了日は期間開始日より後の日付を入力してください')
