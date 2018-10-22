import requests  
import json
import urllib
import re
import random
import telegram 
import datetime
import configuration

from Twilio import Twilio
from dbpostgres import DbHelper
import gspread
from NotificationTable import NotificationTable
from NotificationSheet import NotificationSheet

from LogDBHandler import LogDBHandler
from Actions import Actions
from configuration import ConfigParser
from NotificationNumber import NotificationNumber
from NotificationMessage import NotificationMessage
import time

proxies = {
  'SOCKS4': '91.222.19.167:61221',
}

CONFIG_FILE_NAME = "settings.ini"

class BotHandler:

    #конструктор класса для работы с ботом
    def __init__(self, token):
        self.config=ConfigParser()
        self.config.read(CONFIG_FILE_NAME,"utf_8_sig")
        self.started = True;         
        self.TOKEN = token
        self.URL = "https://api.telegram.org/bot{}/".format(token)
        LogDBHandler.log(Actions.start, configuration.get_database_param("messanger_name"),"", "", "success", "")

    #получает url
    def get_url(self, url, offset=None, timeout=100):
        params = {'timeout': timeout, 'offset': offset}
        response = requests.get(url, params)
        content = response.content.decode("utf8")
        return content

    #вспомогательная функция получает json из url
    def get_json_from_url(self, url):
        content = self.get_url(url)
        js = json.loads(content)
        return js

    #получить все обновления
    def get_updates(self, offset=None, timeout=100):
        url = self.URL + "getUpdates".format(timeout)
        if offset:
            url += "?offset={}".format(offset)
        js = self.get_json_from_url(url)
        return js

    #получить ид последнего обновления
    def get_last_update_id(self, updates):
        update_ids = []
        for update in updates["result"]:
            update_ids.append(int(update["update_id"]))
        return max(update_ids)

    #получить текст и ид чата последнего сообщения
    def get_last_chat_id_and_text(self, updates):
        num_updates = len(updates["result"])
        last_update = num_updates - 1
        text = updates["result"][last_update]["message"]["text"]
        chat_id = updates["result"][last_update]["message"]["chat"]["id"]
        return (text, chat_id)

    #функция ответа на входящие сообщения
    def echo_all(self, updates):
        for update in updates["result"]:  
            try:
                text = update["message"]["text"]
                chat = update["message"]["chat"]["id"]
                LogDBHandler.log(Actions.message, configuration.get_database_param("messanger_name"), self.get_phone_number(chat), text, "success", "user", chat,"","{}", json.dumps(update).replace("'","\""))
                first_name = update["message"]["from"]["first_name"]
                role = self.get_user_role(chat)
                if text=="/start" and self.started:
                    self.subscribe(first_name,chat)
                elif text==configuration.get_database_param("unsubscribe") and self.started:
                    self.unsubscribe(first_name,chat)
                elif text==configuration.get_database_param("disengage") and role=="ADMIN" and self.started==True:
                    self.started=False
                    self.send_message("Работа приостановлена.", chat)
                    LogDBHandler.log(Actions.stop, configuration.get_database_param("messanger_name"), self.get_phone_number(chat), text, "success", "user", chat,"","{}", json.dumps(update).replace("'","\""))
                elif text==configuration.get_database_param("engage") and role=="ADMIN":
                    if self.started==False:
                        self.started=True
                        self.send_message("Бот запущен.", chat)
                        LogDBHandler.log(Actions.start, configuration.get_database_param("messanger_name"), self.get_phone_number(chat), text, "success", "user", chat,"","{}", json.dumps(update).replace("'","\""))
                    else:
                        self.send_message("Бот уже работает!", chat)
                elif text==configuration.get_database_param("list_subscribers") and role=="ADMIN":
                    print(text)
                    self.list_users(first_name,chat)
                elif text==configuration.get_database_param("help"):
                    self.list_help(first_name,chat)
                elif text==configuration.get_database_param("bot_status"):
                    if (self.started==True):
                        self.send_message("Запущен", chat)
                    else:
                        self.send_message("Остановлен", chat)
                elif self.try_process_code(first_name, chat, text)==False:
                    self.send_message(configuration.get_database_param("unknown_comand"),chat)
            except KeyError:
                try:
                    chat = update["message"]["chat"]["id"]
                    first_name = update["message"]["from"]["first_name"]
                    number = update["message"]["contact"]["phone_number"]
                    self.try_process_number(first_name, chat, number)
                except KeyError:
                    chat = update["message"]["chat"]["id"]
                    self.send_message(configuration.get_database_param("unsupported"),chat)
            except Exception as e:
                LogDBHandler.log(Actions.error, configuration.get_database_param("messanger_name"), "", str(e).replace("/","//").replace("'","\""), "fail", "bot", 0,"","{}", json.dumps(update).replace("'","\""))
                print(e)
				
    def list_help(self, first_name, chat_id):
        msg = "Начать работу с ботом: {0}\nОтписаться: {1}\nПомощь: {2}".format("/start", configuration.get_database_param("unsubscribe"), configuration.get_database_param("help"))
        msgadmin = "Запустить бота: {0}\nОстановить бота: {1}\nСтатус бота: {2}\nПолучить список пользователей: {3}".format(configuration.get_database_param("engage"), configuration.get_database_param("disengage"), configuration.get_database_param("bot_status"),configuration.get_database_param("list_subscribers"))
        if self.get_user_role(chat_id)=="ADMIN":
            msg = msg + "\n" + msgadmin
        self.send_message(msg, chat_id)

    #вывести список пользователей
    def list_users(self,  first_name, chat_id):
        result = ""
        db=DbHelper()
        rows = db.execute_select("select user_name, phone_number, chat_id, (select caption from {0}.{1} where id=status), role from {0}.{2}"
                                 .format(
                                     self.config.get("postgresql","schema"),
                                     self.config.get("postgresql","statuse_table"),
                                     self.config.get("postgresql","users_table")))
        for row in rows:
            result+="Имя: {}, Номер: {}, Статус: {}, Роль: {}\n".format(str(row[0]),str(row[1]),str(row[3]),str(row[4]))
        self.send_message(result,chat_id)
    
    #обработка номера телефона
    def try_process_number(self,  first_name, chat_id, number):
        db = DbHelper()
        rows = db.execute_select("SELECT * FROM {}.{} WHERE user_name = '{}' AND chat_id='{}'"
                                 .format(
                                     self.config.get("postgresql","schema"),
                                     self.config.get("postgresql","users_table"),
                                     first_name,
                                     chat_id))
        if len(rows)!=0 and rows[0][4]==1:
            twillio_message = str(random.randint(0,9)) + str(random.randint(0,9)) + str(random.randint(0,9)) + str(random.randint(0,9))
            if (number[0]=="7"):
                number="+" + number
            db.execute_sql("UPDATE {}.{} SET phone_number='{}', sms_code='{}', status={}  WHERE user_name='{}' and chat_id='{}'"
                           .format(
                               self.config.get("postgresql","schema"),
                               self.config.get("postgresql","users_table"),
                               number,
                               twillio_message,
                               2,
                               first_name,
                               chat_id))
            LogDBHandler.log(Actions.phone_number_recieved, configuration.get_database_param("messanger_name"), number, "", "success", "user", chat_id)
            Twilio.send_sms(twillio_message, number)
            LogDBHandler.log(Actions.code_sended,configuration.get_database_param("messanger_name"),number,"","success","bot",chat_id)
            self.send_message(configuration.get_database_param("confirmation_message"), chat_id)

    #обработка кода смс сообщения
    def try_process_code(self,  first_name, chat_id, number):
        db = DbHelper()
        rows = db.execute_select("SELECT * FROM {}.{} WHERE user_name = '{}' AND chat_id='{}'"
                                 .format(
                                     self.config.get("postgresql","schema"),
                                     self.config.get("postgresql","users_table"),
                                     first_name,
                                     chat_id))
        if len(rows)!=0 and rows[0][4]==2:
            try:
                if int(number)==rows[0][5]:
                    db.execute_sql("UPDATE {}.{} SET status={}  WHERE user_name='{}' and chat_id='{}'"
                                   .format(
                                       self.config.get("postgresql","schema"),
                                       self.config.get("postgresql","users_table"),
                                       3,
                                       first_name,
                                       chat_id))
                    self.send_message(configuration.get_database_param("subscribed_message"), chat_id)
                    LogDBHandler.log(Actions.registred,configuration.get_database_param("messanger_name"),self.get_phone_number(chat_id),str(number),"success","bot",chat_id)
                    return True
                else:
                    self.send_message(configuration.get_database_param("wrong_code_message"), chat_id)
                    LogDBHandler.log(Actions.registred,configuration.get_database_param("messanger_name"),self.get_phone_number(chat_id),str(number),"failed","bot",chat_id,"wrong confirmation code")
                    return True
            except Exception as e: 
                self.send_message(configuration.get_database_param("wrong_code_message"), chat_id)
                LogDBHandler.log(Actions.registred,configuration.get_database_param("messanger_name"),self.get_phone_number(chat_id),str(number),"failed","bot",chat_id,"wrong confirmation code")
                return True
        else:
            return False
		
    #получить роль пользователя
    def get_user_role(self, chat_id):
        db = DbHelper()
        rows = db.execute_select("SELECT role FROM {}.{} WHERE chat_id='{}'"
                                 .format(
                                     self.config.get("postgresql","schema"),
                                     self.config.get("postgresql","users_table"),
                                     chat_id))
        if len(rows)!=0:
            return str(rows[0][0])
        else:
            return None
     
    #функция сканирует наличие сообщений в подключенных таблицах и отправляет если есть что оправить       
    def send_notifications(self):
	
        if self.started:
            LogDBHandler.log(Actions.queue, configuration.get_database_param("messanger_name"), "", "Начал цикл", "success", "bot", 0, "")
            db = DbHelper()
            tables_db = db.execute_select("SELECT * FROM {}.{}".format(self.config.get("postgresql","schema"), self.config.get("postgresql","tables_dict")))
            self.tables = []
            for table in tables_db:
                k = 0
                while k < 3:
                    try:
                        self.tables.append(NotificationTable(table[1]))
                    except gspread.exceptions.APIError as e:
                        continue
                    break
            for table in self.tables:
                numbers=[]
                LogDBHandler.log(Actions.queue, configuration.get_database_param("messanger_name"), "", "Начал обработку таблицы. ({})".format(table.table_id), "success", "bot", 0, "")
                for sheet in table.sheets:
                    k = 0
                    while k < 3:
                        k += 1
                        try:						
                            need_send_re = re.compile(r'(' + re.escape(configuration.get_database_param("need_send").strip()) + r')|(' + re.escape(configuration.get_database_param("need_send_sms").strip()) + r')', re.IGNORECASE)
                            #print(sheet.wks.get_all_records())                    
                            list_of_cells = sheet.wks.findall(need_send_re)
                            
                            
                            for cell in list_of_cells:
                                time.sleep(float(configuration.get_database_param("sending_interval"))/2)
                                print(cell.row)
                                row = str(cell.row)
                                sended = sheet.wks.acell(sheet.sended + row).value
                                if sended=="Да": 
                                    continue
                                print("needsend")
                                number = sheet.wks.acell(sheet.number + row).value.replace('-', '').replace('(', '').replace(')', '').replace(' ','')
                                text = sheet.wks.acell(sheet.text + row).value
                                date = sheet.wks.acell(sheet.date + row).value

                                print(date)                                
                                try:
                                    datetime.datetime.strptime(date, '%d/%m/%Y %H:%M:%S')
                                except ValueError:
                                    LogDBHandler.log(Actions.error, configuration.get_database_param("messanger_name"), "", text, "failed", "bot", 0, "Ошибка в таблице: неверный формат даты. Таблица: {0} Лист: {1} Строка: {2} ".format(str(table.table_id), str(sheet.sheet_id), str(row)))
                                    continue

                                print("needsend")
								
                                status = sheet.wks.acell(sheet.status + row).value
                                
                                

                                if len(number)>0:
                                    if (number[0]=="7"):
                                        number="+" + number
                                    elif (number[0]=="8"):
                                        number = number.replace("8","+7",1)            
                                else:
                                    LogDBHandler.log(Actions.error, configuration.get_database_param("messanger_name"), "", text, "failed", "bot", 0, "Ошибка в таблице: не заполнен номер телефона в таблице. Таблица: {0} Лист: {1} Строка: {2} ".format(str(table.table_id), str(sheet.sheet_id), str(row)))
                                    continue

                                if any(x.phone_number == number for x in numbers)==False and sended != "Да":
                               	    notification_number = NotificationNumber(number,sheet)
                                    notification_number.messages.append(NotificationMessage(date,status,sended,text,row))
                                    numbers.append(notification_number)
                                else:
                                    for x in numbers:
                                        if x.phone_number==number:
                                            notification_number = x
                                    notification_number.messages.append(NotificationMessage(date,status,sended,text,row))
                                
                        except gspread.exceptions.APIError as e:
                            sheet.refresh()
                            print(sheet.sheet_id + ";" + sheet.table_id)
                            print(e)
                            continue
                        break
                        
                    
                for number in numbers:
                    number.sort_by_date()
                    print(number.phone_number)
                    for message in number.messages:
                        print(message.date)
                LogDBHandler.log(Actions.queue, configuration.get_database_param("messanger_name"), "", "Таблицу обработал ({}). Начинаю отправку сообщений.".format(str(table.table_id)), "success", "bot", 0, "")			
                for number in numbers:
                    number.sort_by_date()
                    for message in number.messages:
                        print(number.phone_number + ";" + message.date + ";" + message.text + ";" + message.status + ";" + message.sended + ";" + message.row)
                        i=0
                        while i < 3:
                            i += 1
                            try:
                                            
                                db = DbHelper()
                                dbrows = db.execute_select("SELECT chat_id FROM {}.{} where phone_number='{}' and status=3"
                                                            .format(
                                                                self.config.get("postgresql","schema"),
                                                                self.config.get("postgresql","users_table"),
                                                                number.phone_number))
                                if len(dbrows) != 0:
                                    
                                    chat_id = dbrows[0][0]
                                    if message.sended != "Да":
                                        print("Sending...")
                                        if (configuration.get_database_param("need_send_sms").strip().lower()==str(message.status).lower()) and Twilio.send_sms(message.text,number.phone_number):
                                            number.sheet.wks.update_acell(number.sheet.sended+message.row,"Да")
                                            print("Sended sms")
                                        elif (configuration.get_database_param("need_send").strip().lower()==str(message.status).lower()) and self.send_message(message.text,chat_id):
                                            print("Sended telegram")
                                            number.sheet.wks.update_acell(number.sheet.sended+message.row,"Да")
                                else:
                                    LogDBHandler.log(Actions.error, configuration.get_database_param("messanger_name"), number.phone_number, message.text, "failed", "bot", 0, "Ошибка в таблице: пользователь не зарегистрирован. Таблица: {0} Лист: {1} Строка: {2} ".format(str(table.table_id), str(number.sheet.sheet_id), str(message.row)))
                                time.sleep(float(configuration.get_database_param("sending_interval"))/2)
                            except gspread.exceptions.APIError as e:
                                number.sheet.refresh()
                                continue
                            break
                LogDBHandler.log(Actions.queue, configuration.get_database_param("messanger_name"), "", "Отправку сообщений по таблице закончил ({})".format(table.table_id), "success", "bot", 0, "")
            LogDBHandler.log(Actions.queue, configuration.get_database_param("messanger_name"), "", "Цикл отправки завершил.", "success", "bot", 0, "")

                           
    #вспомогательная функция для кастомной клавиатуры                        
    def build_keyboard(self, text):
        keyboard = [[{"text": text,"request_contact": True}]]
        reply_markup = {"keyboard":keyboard, "one_time_keyboard": True, "resize_keyboard": True}
        return json.dumps(reply_markup)
		
    #def build_admin_keyboard(self):
    #   keyboard = [[{"text":configuration.get_database_param( "engage"),"callback_data":"1"},{"text":configuration.get_database_param( "disengage"),"callback_data":"2"},{"text":configuration.get_database_param( #"bot_status"),"callback_data":"3"},{"text":configuration.get_database_param("list_subscribers"),"callback_data":"3"}]]
    #   reply_markup = {"keyboard":keyboard, "resize_keyboard": True}
    #    return json.dumps(reply_markup)
		
    #(подписать пользователя (добавить в БД)
    def subscribe(self, first_name, chat_id):
        db = DbHelper()
        rows = db.execute_select("SELECT * FROM {}.{} WHERE user_name = '{}' AND chat_id = '{}'"
                                 .format(
                                     self.config.get("postgresql","schema"),
                                     self.config.get("postgresql","users_table"),
                                     first_name,
                                     chat_id))
        if len(rows)==0:
            db.execute_sql("INSERT INTO {}.{} (user_name, chat_id, status) VALUES ('{}', '{}', {})"
                           .format(
                               self.config.get("postgresql","schema"),
                               self.config.get("postgresql","users_table"),
                               first_name,
                               chat_id,
                               1))
            #keyboard = self.build_keyboard(telegram.KeyboardButton(text="Поделиться номером телефона", request_contact=True))
           
            self.send_message(configuration.get_database_param("share_number_message"), chat_id, self.build_keyboard(configuration.get_database_param("button_caption")))
        else:
            self.send_message(configuration.get_database_param("already_subscribed_message"), chat_id)
    
    #отписать пользователя (удалить из БД)
    def unsubscribe(self, first_name, chat_id):
        phone_number = self.get_phone_number(chat_id)
        try:
            
            db = DbHelper()
            db.execute_sql("DELETE FROM {}.{} WHERE user_name = '{}' AND phone_number = '{}'"
                           .format(
                               self.config.get("postgresql","schema"),
                               self.config.get("postgresql","users_table"),
                               first_name,
                               phone_number))
            LogDBHandler.log(Actions.unsubscribed, configuration.get_database_param("messanger_name"), phone_number, "", "success", "bot", chat_id)
            self.send_message(configuration.get_database_param("unsubscribed_message"), chat_id)
        except Exception as e:
            LogDBHandler.log(Actions.unsubscribed, configuration.get_database_param("messanger_name"), phone_number, str(e).replace("/","//").replace("'","\""), "failed", "bot", chat_id)

    #отправка сообщения
    def send_message(self, text, chat_id, reply_markup=None):
        response = '{}'
        try:
            unparsedtext = text
            print(text)
            text = urllib.parse.quote_plus(text)
            url = self.URL + "sendMessage?text={}&chat_id={}&parse_mode=HTML".format(text, chat_id)
            #role = self.get_user_role(chat_id)
            #if role=="ADMIN":
            #    reply_markup = self.build_admin_keyboard()
            if reply_markup:
                url += "&reply_markup={}".format(reply_markup)
            response = self.get_url(url)
            print(url)
            
            LogDBHandler.log(Actions.message, configuration.get_database_param("messanger_name"), self.get_phone_number(chat_id), unparsedtext[0:100], "success", "bot", chat_id, "",json.dumps(url) ,json.dumps(response.replace("'", '\\"')))
            return True
        except  Exception as e:
            LogDBHandler.log(Actions.message, configuration.get_database_param("messanger_name"), self.get_phone_number(chat_id), unparsedtext[0:100], "failed", "bot", chat_id, str(e).replace("/","//").replace("'","\""), json.dumps(url), json.dumps(response.replace("'", '\\"')))
            return False

    def get_phone_number(self, chat_id):
        db = DbHelper()
        rows = db.execute_select("SELECT phone_number FROM {}.{} WHERE chat_id='{}'"
                                 .format(
                                     self.config.get("postgresql","schema"),
                                     self.config.get("postgresql","users_table"),
                                     chat_id))
        if len(rows)!=0:
            return str(rows[0][0])
        else:
            return ""
