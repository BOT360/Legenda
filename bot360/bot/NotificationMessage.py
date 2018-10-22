import datetime

class NotificationMessage:

    def __init__(self,date,status,sended,text,row):
        self.date=date
        self.status=status
        self.sended=sended
        self.text=text
        self.row=row