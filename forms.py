from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, DecimalField, DateField, TextAreaField, SelectField, HiddenField, BooleanField
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
    customer_name = StringField('顧客名', validators=[
        DataRequired(message='顧客名は必須です'),
        Length(max=200, message='顧客名は200文字以下で入力してください')
    ])
    project_name = StringField('プロジェクト名', validators=[
        DataRequired(message='プロジェクト名は必須です'),
        Length(max=200, message='プロジェクト名は200文字以下で入力してください')
    ])
    sales_amount = DecimalField('売上金額', validators=[
        DataRequired(message='売上金額は必須です'),
        NumberRange(min=0, message='売上金額は0以上で入力してください')
    ], widget=NumberInput(step='1'))
    order_amount = DecimalField('受注金額', validators=[
        DataRequired(message='受注金額は必須です'),
        NumberRange(min=0, message='受注金額は0以上で入力してください')
    ], widget=NumberInput(step='1'))
    invoiced_amount = DecimalField('請求金額', validators=[
        DataRequired(message='請求金額は必須です'),
        NumberRange(min=0, message='請求金額は0以上で入力してください')
    ], widget=NumberInput(step='1'))
    order_date = DateField('受注日', validators=[
        DataRequired(message='受注日は必須です')
    ])
    contract_type = SelectField('契約形態', choices=[
        ('準委任', '準委任'),
        ('請負', '請負'),
        ('派遣', '派遣'),
        ('その他', 'その他')
    ], validators=[Optional()])
    sales_stage = SelectField('案件ステージ', choices=[
        ('提案中', '提案中'),
        ('受注済', '受注済'),
        ('失注', '失注'),
        ('完了', '完了')
    ], validators=[Optional()])
    billing_month = DateField('請求月', validators=[
        Optional()
    ])
    work_in_progress = BooleanField('進行中', default=False)
    description = TextAreaField('詳細', validators=[
        Optional(),
        Length(max=2000, message='詳細は2000文字以下で入力してください')
    ])
