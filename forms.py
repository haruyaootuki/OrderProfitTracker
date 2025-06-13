from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, IntegerField, DateField, TextAreaField, SelectField, HiddenField, BooleanField
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

def validate_amount(form, field):
    if field.data:
        # 文字列の場合、カンマを除去して数値に変換
        if isinstance(field.data, str):
            try:
                value = int(field.data.replace(',', ''))
                if value < 0 or value > 1000000000:
                    raise ValidationError('金額は0円以上10億円以下で入力してください')
                field.data = value
            except ValueError:
                raise ValidationError('有効な数値を入力してください')

class OrderForm(FlaskForm):
    id = HiddenField()
    customer_name = StringField('顧客名', validators=[
        DataRequired(message='顧客名は必須です'),
        Length(max=200, message='顧客名は200文字以下で入力してください')
    ])
    project_name = StringField('案件名', validators=[
        DataRequired(message='案件名は必須です'),
        Length(max=200, message='案件名は200文字以下で入力してください')
    ])
    sales_amount = StringField('売上金額', validators=[
        Optional(),
        validate_amount
    ], widget=NumberInput(step='1'), default='0', render_kw={"type": "text", "max": "1000000000"})
    order_amount = StringField('受注金額', validators=[
        Optional(),
        validate_amount
    ], widget=NumberInput(step='1'), default='0', render_kw={"type": "text", "max": "1000000000"})
    invoiced_amount = StringField('請求金額', validators=[
        Optional(),
        validate_amount
    ], widget=NumberInput(step='1'), default='0', render_kw={"type": "text", "max": "1000000000"})
    order_date = DateField('受注日', validators=[
        DataRequired(message='受注日は必須です')
    ])
    contract_type = StringField('契約形態', validators=[
        Optional(),
        Length(max=16, message='契約形態は16文字以下で入力してください')
    ])
    sales_stage = StringField('確度', validators=[
        Optional(),
        Length(max=16, message='確度は16文字以下で入力してください')
    ])
    billing_month = DateField('請求日', validators=[
        Optional()
    ])
    work_in_progress = BooleanField('仕掛', default=False)
    description = TextAreaField('詳細', validators=[
        Optional(),
        Length(max=2000, message='詳細は2000文字以下で入力してください')
    ])
