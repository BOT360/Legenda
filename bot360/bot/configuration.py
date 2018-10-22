from configparser import ConfigParser
from dbpostgres import DbHelper

CONFIG_FILE_NAME = "settings.ini"
config = ConfigParser()
config.read(CONFIG_FILE_NAME,"utf_8_sig")
	
def config(filename, section):
    db = {}
    if parser.has_section(section):
        params = parser.items(section)
        for param in params:
            db[param[0]] = param[1]
    else:
        raise Exception('Section {0} not found in the {1} file'.format(section, filename))
    
    return db

def get_database_param(param_name):
    db = DbHelper()
    rows = db.execute_select("SELECT param_value FROM {}.{} WHERE param_name = '{}'"
                                 .format(
                                     "notificator",
                                     "params",
                                     param_name))
    return rows[0][0]