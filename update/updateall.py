import threading
import time
import commands
import logging

def update(server):
    (status,output)=commands.getstatusoutput('./updateone %s' % server)
    if status>0:
        logging.error('run updateone fail:%s' % output)
    else:
        logging.info('OK,%s' % output)

logging.basicConfig(level=logging.DEBUG)

threads=[]
start_time=time.time()
threads.append(threading.Thread(target=update,args=("_19j.boosoo.cn",)))
threads.append(threading.Thread(target=update,args=("_19j2.boosoo.cn",)))
threads.append(threading.Thread(target=update,args=("_19j3.boosoo.cn",)))
threads.append(threading.Thread(target=update,args=("_19j4.boosoo.cn",)))
threads.append(threading.Thread(target=update,args=("_19u.boosoo.cn",)))
threads.append(threading.Thread(target=update,args=("_19u2.boosoo.cn",)))
threads.append(threading.Thread(target=update,args=("_19u3.boosoo.cn",)))
threads.append(threading.Thread(target=update,args=("_19u4.boosoo.cn",)))
threads.append(threading.Thread(target=update,args=("_19u5.boosoo.cn",)))
threads.append(threading.Thread(target=update,args=("_19u6.boosoo.cn",)))
threads.append(threading.Thread(target=update,args=("de1.boosoo.cn",)))
threads.append(threading.Thread(target=update,args=("ru1.boosoo.cn",)))
threads.append(threading.Thread(target=update,args=("ph1.boosoo.cn",)))
threads.append(threading.Thread(target=update,args=("jinwang.vip.boosoo.cn",)))
threads.append(threading.Thread(target=update,args=("_eam.vip.boosoo.cn",)))
threads.append(threading.Thread(target=update,args=("_yawoo.vip.boosoo.cn",)))

for t in threads:
    t.start()

for t in threads:
    t.join()

end_time=time.time()
logging.info('total spend %s second' % str(end_time-start_time))
