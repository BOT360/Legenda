from BotHandler import BotHandler
from multiprocessing import Pool
from multiprocessing import Process
from configuration import ConfigParser
import threading

import time

CONFIG_FILE_NAME = "settings.ini"
config=ConfigParser()
config.read(CONFIG_FILE_NAME,"utf_8_sig")
bot = BotHandler(config.get("botsettings","token"))  


def main():
    #p = Process(target=answer)
    #p.start()
    #p.join()
    #p2 = Process(target=notificate)
    #p2.start()
    #p2.join()
    #pool = Pool()
    #pool.apply_async(notificate)
    #pool.apply_async(answer)
    #answer()
	threading.Thread(target=notificate).start()
	threading.Thread(target=answer).start()
    #notificate()
    
def notificate():
    while True:
        bot.send_notifications()
        time.sleep(5)

def answer():
    last_update_id = None
    while True:
        updates = bot.get_updates(last_update_id)
        if len(updates["result"]) > 0:
            last_update_id = bot.get_last_update_id(updates) + 1
            bot.echo_all(updates)
        time.sleep(0.5)

if __name__ == '__main__':
    main()
