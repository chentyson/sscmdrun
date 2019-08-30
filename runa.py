import os
import commands
import time
import logging

while True:
    if os.path.exists('/tmp/supervisor.sock'):
        time.sleep(60)
    else:
        (status,output) = commands.getstatusoutput('systemctl restart supervisord')
        logging.warning('Found no exists supervisor.sock, try to restarted:%s' % output)
        if status>0:
            logging.warning('Fail~~')
        else:
            logging.warning('ok')
        time.sleep(5) 


