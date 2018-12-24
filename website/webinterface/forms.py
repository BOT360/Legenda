from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField, FieldList, FormField, IntegerField, HiddenField, TextField
from wtforms.validators import DataRequired, Length


class LoginForm(FlaskForm):
    username = StringField('Имя пользователя', validators=[
                           DataRequired(), Length(min=2, max=20)])
    password = PasswordField('Пароль', validators=[DataRequired()])
    remember = BooleanField('Запомнить меня')
    submit = SubmitField('Войти')


class SheetForm(FlaskForm):
    date_col = StringField('Столбец с датой', validators=[
        DataRequired()])
    status_col = StringField('Столбец со статусом', validators=[
        DataRequired()])
    sended_col = StringField('Столбец отправлено', validators=[
        DataRequired()])
    text_col = StringField('Столбец с текстом сообщения', validators=[
        DataRequired()])
    number_col = StringField('Столбец с номером телефона', validators=[
        DataRequired()])
    table_id = StringField('Столбец с номером телефона', validators=[
        DataRequired()])
    sheet_name = StringField('Столбец с именем листа', validators=[
        DataRequired()])


class TableForm(FlaskForm):
    spreadsheet_id = TextField('Идентификатор таблицы', validators=[
        DataRequired()])
    sheets = FieldList(FormField(SheetForm))


class TablesForm(FlaskForm):
    tables = FieldList(FormField(TableForm))


class SettingForm(FlaskForm):
    param_name = StringField('Имя параметра', validators=[
        DataRequired()])
    param_value = StringField('Значение параметра', validators=[
        DataRequired()])


class SettingsForm(FlaskForm):
    settings = FieldList(FormField(SettingForm))
    submit = SubmitField('Сохранить')
