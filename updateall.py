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
threads.append(threading.Thread(target=update,args=("19j.boosoo.cn",)))
threads.append(threading.Thread(target=update,args=("19j2.boosoo.cn",)))
#threads.append(threading.Thread(target=update,args=("19j3.boosoo.cn",)))
threads.append(threading.Thread(target=update,args=("19j4.boosoo.cn",)))
threads.append(threading.Thread(target=update,args=("19u.boosoo.cn",)))
threads.append(threading.Thread(target=update,args=("19u2.boosoo.cn",)))
threads.append(threading.Thread(target=update,args=("19u3.boosoo.cn",)))
threads.append(threading.Thread(target=update,args=("19u4.boosoo.cn",)))
threads.append(threading.Thread(target=update,args=("vip2.boosoo.cn",)))
threads.append(threading.Thread(target=update,args=("19h.boosoo.cn",)))
threads.append(threading.Thread(target=update,args=("jinwang.vip.boosoo.cn",)))
threads.append(threading.Thread(target=update,args=("eam.vip.boosoo.cn",)))
threads.append(threading.Thread(target=update,args=("lktools.vip.boosoo.cn",)))
threads.append(threading.Thread(target=update,args=("yawoo.vip.boosoo.cn",)))
threads.append(threading.Thread(target=update,args=("yk.vip.boosoo.cn",)))
threads.append(threading.Thread(target=update,args=("jy.vip.boosoo.cn",)))

for t in threads:
    t.start()

for t in threads:
    t.join()

end_time=time.time()
logging.info('total spend %s second' % str(end_time-start_time))
