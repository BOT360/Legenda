import gspread
from oauth2client.service_account import ServiceAccountCredentials

class NotificationSheet:
    def __init__(self, date, status, sended, text, number, table_id, sheet_id):
        scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
        self.credentials = ServiceAccountCredentials.from_json_keyfile_name('bot360-6b65381d463a.json', scope)
        self.gc = gspread.authorize(self.credentials)
        self.date = date
        self.status = status
        self.sended=sended
        self.text=text
        self.number=number
        self.table_id=table_id
        self.sheet_id=sheet_id
        self.wks = self.gc.open_by_key(self.table_id).worksheet(self.sheet_id)
		
    def refresh(self):
        print("refreshing")
        if self.credentials.access_token_expired or self.credentials is None or self.credentials.invalid:
            scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
            self.credentials = ServiceAccountCredentials.from_json_keyfile_name('bot360-6b65381d463a.json', scope)
            self.gc = gspread.authorize(self.credentials)
            self.wks = self.gc.open_by_key(self.table_id).worksheet(self.sheet_id)
