from webinterface import db, login_manager
from flask_login import UserMixin


@login_manager.user_loader
def load_user(user_id):
    return web_users.query.get(int(user_id))


class web_users(db.Model, UserMixin):
    __table_args__ = ({"schema": "notificator"})
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), nullable=False)
    password = db.Column(db.String(60), nullable=False)

    def __repr__(self):
        return f"web_users('{self.username}', '{self.password}')"


class users(db.Model, UserMixin):
    __table_args__ = ({"schema": "notificator"})
    id = db.Column(db.Integer, primary_key=True)
    user_name = db.Column(db.String(255), nullable=False)
    phone_number = db.Column(db.String(255), nullable=False)
    chat_id = db.Column(db.String(255), nullable=False)
    status = db.Column(db.String(255), nullable=False)
    sms_code = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(255), nullable=False)

    @property
    def serialize(self):
        """Return object data in easily serializeable format"""
        return {
            'id': self.id,
            'user_name': self.user_name,
            'phone_number': self.phone_number,
            'chat_id': self.chat_id,
            'status': self.status,
            'sms_code': self.sms_code,
            'role': self.role,
        }


class google_tables(db.Model):
    __table_args__ = ({"schema": "notificator"})
    id = db.Column(db.Integer, primary_key=True)
    spreadsheet_id = db.Column(db.String(255), nullable=False)
    sheets = db.relationship(
        'google_sheets', cascade="all,delete", backref='parent')

    def __repr__(self):
        return f"google_table('{self.spreadsheet_id}')"

    @property
    def serialize(self):
        """Return object data in easily serializeable format"""
        return {
            'id': self.id,
            'spreadsheet_id': self.spreadsheet_id
        }


class params(db.Model):
    __table_args__ = ({"schema": "notificator"})
    id = db.Column(db.Integer, primary_key=True)
    param_name = db.Column(db.String(255), nullable=False)
    param_value = db.Column(db.String(255), nullable=False)
    display_name = db.Column(db.String(255), nullable=False)

    def __repr__(self):
        return f"params('{self.param_name}', '{self.param_value}')"


class google_sheets(db.Model):
    __table_args__ = ({"schema": "notificator"})
    id = db.Column(db.Integer, primary_key=True)
    date_col = db.Column(db.String(255), nullable=False)
    status_col = db.Column(db.String(255), nullable=False)
    sended_col = db.Column(db.String(255), nullable=False)
    text_col = db.Column(db.String(255), nullable=False)
    number_col = db.Column(db.String(255), nullable=False)
    table_id = db.Column(db.Integer, db.ForeignKey(
        google_tables.id), nullable=False)
    sheet_name = db.Column(db.String(255))

    def __repr__(self):
        return f"google_sheet('{self.date_col}','{self.status_col}','{self.sended_col}','{self.text_col}','{self.number_col}','{self.table_id}','{self.sheet_name}')"


class logs(db.Model):
    __table_args__ = ({"schema": "notificator"})
    id = db.Column(db.Integer, primary_key=True)
    action_ = db.Column(db.String(40), nullable=False)
    messenger = db.Column(db.String(20), nullable=True)
    phone_number = db.Column(db.String(255), nullable=True)
    message = db.Column(db.String(255), nullable=True)
    date_time = db.Column(db.DateTime(timezone=False), nullable=True)
    sended_json = db.Column(db.JSON, nullable=True)
    recieved_json = db.Column(db.JSON, nullable=True)
    result = db.Column(db.String(20), nullable=True)
    direction = db.Column(db.String, nullable=True)
    user_id = db.Column(db.Integer, nullable=True)
    additional_info = db.Column(db.String(1000), nullable=True)

    @property
    def serialize(self):
        """Return object data in easily serializeable format"""
        return {
            'id': self.id,
            'action_': self.action_,
            'messenger': self.messenger,
            'phone_number': self.phone_number,
            'message': self.message,
            'date_time': self.date_time.strftime('%d/%m/%Y %H:%M:%S'),
            'recieved_json': self.recieved_json,
            'result': self.result,
            'direction': self.direction,
            'additional_info': self.additional_info
        }
