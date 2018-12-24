from flask import render_template, url_for, redirect, flash, request, jsonify, g, session
from webinterface import app, bcrypt, db
from formencode import variabledecode
from webinterface.forms import LoginForm, TablesForm, TableForm, SheetForm, SettingForm, SettingsForm
from webinterface.models import web_users, google_sheets, google_tables, params, logs, users
from flask_login import login_user, current_user, logout_user, login_required
from sqlalchemy import and_, update, func
import datetime


posts = [
    {
        'author': 'Boyarshinov Roman',
        'title': 'Blog Post 1',
        'content': 'First post content',
        'date_posted': 'April 20, 2018'
    },
    {
        'author': 'Vlasov Evgeniy',
        'title': 'Blog Post 2',
        'content': 'Second post content',
        'date_posted': 'April 23, 2018'
    }
]


def get_logs_date_from():
    logs_date_from = session.get('logs_date_from', None)
    if logs_date_from is None:
        session['logs_date_from'] = datetime.datetime.now().strftime('%Y-%m-%d')
    return session['logs_date_from']


def set_logs_date_from(logs_date_from):
    session['logs_date_from'] = logs_date_from
    return logs_date_from


def get_logs_date_to():
    logs_date_to = session.get('logs_date_to', None)
    if logs_date_to is None:
        session['logs_date_to'] = datetime.datetime.now().strftime('%Y-%m-%d')
    return session['logs_date_to']


def set_logs_date_to(logs_date_to):
    session['logs_date_to'] = logs_date_to
    return logs_date_to


def get_developer_mode():
    developer_mode = session.get('developer_mode', None)
    if developer_mode is None:
        session['developer_mode'] = False
    return session['developer_mode']


def set_developer_mode(developer_mode):
    session['developer_mode'] = developer_mode
    return developer_mode


@app.route("/", methods=['GET', 'POST'])
@app.route("/home", methods=['GET', 'POST'])
@app.route("/tables", methods=['GET', 'POST'])
@login_required
def home():
    if request.method == 'POST':
        postvars = variabledecode.variable_decode(request.form, dict_char='_')

        print(postvars)

        for k, v in postvars.items():
            if (('gtable' in k) or ('spreadsheet' in k)):
                for vname in v:
                    if (v[vname] == '' or v[vname] == None):
                        flash('Нельзя оставлять поля пустыми!', 'danger')
                        return redirect(url_for('home'))

        for k, v in postvars.items():
            if ('deletedsheet' in k):
                t_id = v['id']
                if (('new' not in t_id) and (google_sheets.query.filter(
                        google_sheets.id == t_id) != None)):
                    sheet_delete = google_sheets.query.filter(
                        google_sheets.id == t_id)[0]
                    db.session.delete(sheet_delete)
                    db.session.commit()

            if ('deletedtable' in k):
                t_id = v['id']
                if (('new' not in k) and (google_tables.query.filter(
                        google_tables.id == t_id) != None)):
                    table_delete = google_tables.query.filter(
                        google_tables.id == t_id)[0]
                    db.session.delete(table_delete)
                    db.session.commit()

            if ('gtable' in k):
                t_id = v['id']
                if ('new' in t_id):
                    new_table = google_tables(
                        spreadsheet_id=v['spreadsheetid'])
                    db.session.add(new_table)
                    db.session.commit()
                    new_id = new_table.id
                    for k1, v1 in postvars.items():
                        if (('spreadsheet' in k1) and (v1['tableid'] in t_id)):
                            v1['tableid'] = new_id

                elif (google_tables.query.filter(
                        google_tables.id == t_id) != None):
                    existing_table = google_tables.query.filter(
                        google_tables.id == t_id)[0]

                    if existing_table.spreadsheet_id != v['spreadsheetid']:
                        google_tables.query.filter(google_tables.id == existing_table.id).update({
                            'spreadsheet_id': v['spreadsheetid']})
                        db.session.commit()

            if ('spreadsheet' in k):
                t_id = v['id']
                if (t_id == 'new'):
                    new_sheet = google_sheets(
                        date_col=v['datecol'],
                        status_col=v['statuscol'],
                        sended_col=v['sendedcol'],
                        text_col=v['textcol'],
                        number_col=v['numbercol'],
                        table_id=v['tableid'],
                        sheet_name=v['sheetname'])
                    db.session.add(new_sheet)
                    db.session.commit()
                elif (google_sheets.query.filter(
                        google_sheets.id == t_id) != None):
                    existing_sheet = google_sheets.query.filter(
                        google_sheets.id == t_id)[0]
                    google_sheets.query.filter(google_sheets.id == existing_sheet.id).update({
                        'date_col': v['datecol'],
                        'status_col': v['statuscol'],
                        'sended_col': v['sendedcol'],
                        'text_col': v['textcol'],
                        'number_col': v['numbercol'],
                        'sheet_name': v['sheetname'],
                    })
                    db.session.commit()

        return redirect(url_for('home'))
    else:
        tables = google_tables.query.order_by(
            google_tables.id.asc()).all()

        sheets = google_sheets.query.order_by(
            google_sheets.id.asc()).all()

        return render_template('home.html', google_tables=tables, google_sheets=sheets)


@app.route("/about")
@login_required
def about():
    return render_template('about.html', title='Информация')


@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for('login'))


@app.route("/settings", methods=['GET', 'POST'])
@login_required
def settings():

    if request.method == 'POST':
        postvars = variabledecode.variable_decode(request.form, dict_char='_')
        for k, v in postvars.items():
            if ('param' in k):
                t_id = v['id']
                if (params.query.filter(
                        params.id == t_id) != None):
                    param = params.query.filter(
                        params.id == t_id)[0]

                    if param.param_value != v['paramvalue']:
                        params.query.filter(params.id == param.id).update({
                            'param_value': v['paramvalue']})
                        db.session.commit()

    settings = params.query.order_by(
        params.id.asc()).all()

    return render_template('settings.html', settings=settings)


@app.route("/login", methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = web_users.query.filter_by(username=form.username.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user, remember=form.remember.data)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('home'))
        else:
            flash('Неверное имя пользователя или пароль', 'danger')
    return render_template('login.html', title='Вход', form=form)


@app.route("/get_logs")
def get_logs():
    logs_date_from = get_logs_date_from()
    logs_date_to = get_logs_date_to()
    developer_mode = get_developer_mode()

    date_from = datetime.datetime.strptime(logs_date_from, '%Y-%m-%d')
    date_to = datetime.datetime.strptime(
        logs_date_to, '%Y-%m-%d') + datetime.timedelta(days=1)

    if (developer_mode == True):
        json_list = [i.serialize for i in logs.query.filter(logs.date_time >= date_from, logs.date_time <= date_to).order_by(
            logs.id.desc()).all()]
        return jsonify(json_list)
    else:
        json_list = [i.serialize for i in logs.query.filter(logs.date_time >= date_from, logs.date_time <= date_to, logs.action_ != 'QUEUE', logs.action_ != 'STARTED').order_by(
            logs.id.desc()).all()]
        return jsonify(json_list)


@app.route("/get_users")
def get_users():
    json_list = [i.serialize for i in users.query.order_by(
        users.id.desc()).all()]
    return jsonify(json_list)


@app.route("/show_users", methods=['GET', 'POST'])
def show_users():
    if request.method == 'POST':
        try:
            postvars = variabledecode.variable_decode(
                request.form, dict_char='_')
            users.query.filter(users.phone_number == postvars['phoneNumber']).update({
                'role': postvars['role']})
            db.session.commit()
        except Exception:
            flash('Пользователь не зарегистрирован!', 'danger')

    return render_template('users.html', title='Пользователи')


@app.route("/show_logs", methods=['GET', 'POST'])
def show_logs():

    logs_date_from = get_logs_date_from()
    logs_date_to = get_logs_date_to()
    developer_mode = get_developer_mode()

    if request.method == 'POST':
        postvars = variabledecode.variable_decode(request.form, dict_char='_')
        logs_date_from = postvars['dateFrom']
        logs_date_to = postvars['dateTo']
        if (('developerMode' in postvars) and postvars['developerMode'] == 'on'):
            developer_mode = True
        else:
            developer_mode = False
        set_logs_date_from(logs_date_from)
        set_logs_date_to(logs_date_to)
        set_developer_mode(developer_mode)
        return render_template('logs.html', title='Логи', dateFrom=logs_date_from, dateTo=logs_date_to, devMode=developer_mode)
    else:
        logs_date_from = datetime.datetime.now().strftime('%Y-%m-%d')
        logs_date_to = datetime.datetime.now().strftime('%Y-%m-%d')
        developer_mode = False
        set_logs_date_from(logs_date_from)
        set_logs_date_to(logs_date_to)
        set_developer_mode(developer_mode)
        return render_template('logs.html', title='Логи', dateFrom=logs_date_from, dateTo=logs_date_to, devMode=developer_mode)
