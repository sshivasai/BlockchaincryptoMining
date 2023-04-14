from wtforms import Form, StringField, DecimalField, IntegerField, TextAreaField, PasswordField, validators

#form used on Register page
class RegisterForm(Form):
    name = StringField('Full Name', [validators.Length(min=1,max=50)])
    username = StringField('Username', [validators.Length(min=4,max=25)])
    email = StringField('Email', [validators.Length(min=6,max=50)])
    password = PasswordField('Password', [validators.DataRequired(), validators.EqualTo('confirm', message='Passwords do not match')])
    confirm = PasswordField('Confirm Password')

#form used on the Transactions page
class SendMoneyForm(Form):
    username = StringField('Username', [validators.Length(min=4,max=25)])
    amount = StringField('Amount', [validators.Length(min=1,max=50)])
    random_text = StringField('Type your Text', [validators.Length(min=1,max=500)],default="")
#form used on the Buy page
class BuyForm(Form):
    amount = StringField('Amount', [validators.Length(min=1,max=50)])
    random_text = StringField('Type your Text', [validators.Length(min=1,max=500)],default="")



class MineForm(Form):
    start_block = StringField( '', [validators.Length(min=1,max=500)],default=" ")
    target_block = StringField( '', [validators.Length(min=1,max=500)],default=" ")
    amount = StringField('',[validators.Length(min=1,max=50)],default=1)
    max_try =  StringField('',[validators.Length(min=1,max=50)],default=10000)