from NotificationMessage import NotificationMessage

class NotificationNumber:
	
    def __init__(self, phone_number, sheet):
        self.phone_number=phone_number
        self.messages=[]
        self.sheet=sheet

    def sort_by_date(self):
        self.messages.sort(key=lambda x: x.date)