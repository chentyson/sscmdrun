import os
import commands
import time
import logging
import ssmail
import config

myconfig = config.config()
tried = 0

while True:
    if os.path.exists('/tmp/supervisor.sock'):
        time.sleep(5)
    else:
        (status,output) = commands.getstatusoutput('systemctl restart supervisord')
        logging.warning('Found no exists supervisor.sock, try to restarted:%s' % output)
        if status>0:
            logging.warning('Fail~~')
            tried=tried+1
            if tried==5 or tried==12 or tried==60 or tried==120:
                logging.warning('many times tried, fail~, help')
                ssmail.mail('Supervior fail to start %s times~ (' + myconfig.getaid(10000) + ')','Found no exists supervisor.sock, try to restart it many times, buy, fail, help~', '', 'info@boosoo.cn' )
        else:
            tried = 0
            logging.warning('ok')
            ssmail.mail('Supervisor restarted.(' + myconfig.getaid(10000) + ')','Found no exists supervisor.sock,restarted done!', '', 'info@boosoo.cn')
        time.sleep(5) 


