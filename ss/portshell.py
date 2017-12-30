# coding=utf-8
import cfgshell
import time

def portpass(config):
    return config.get('port_password');  

#增加一个端口，正式或测试，用户允许同时在线的 ip 数，如果ip数的端口范围满了，则返回端口号是 0
def add_new_port(config,newpass,payortest,ipnums):
    configport = portpass(config) 
    if ipnums<1: ipnums=1;
    elif ipnums>9: ipnubs=9;
    portstart=10001 + ipnums*1000; 
    portend=10999 + ipnums*1000;
    for i in range(portstart,portend):
        if not configport.has_key(str(i)):
            if payortest=='pay':
   	          configport[str(i)]=newpass+'-'+time.strftime('%y%m%d');
            elif payortest=='test':
   	          configport[str(i)]=newpass+'-test';
            else: configport[str(i)]=newpass;
	    return str(i),configport[str(i)];
    return '0',''

def status_port(config,port,status):
    lists=portpass(config)
    if lists.has_key(port):
        passwd=lists[port]
        passlist=passwd.split('-')
        if len(passlist)==1: newpass=passlist[0]+'-'+status; 
        elif len(passlist)>1: newpass=passwd[:passwd.rindex('-')]+'-'+status
        else: return '0','This port has no default password,cannot pay,please delete it and re-add again.'
        lists[port]=newpass
        return port,newpass
    else: return '0','Can not find port[%s]!' % port

def pay_port(config,port):
    return status_port(config,port,time.strftime('%y%m%d'))

def stop_port(config,port):
    return status_port(config,port,'stop')

def find_port(config,port):
    lists=portpass(config)
    if lists.has_key(port):
        return port,lists.get(port)
    for key,value in lists.items():
        if value.find(port)!=-1:
            return(key,value)
    return (0,'')

def count_port(config,status):
    lists=portpass(config);
    if status=='':
        return len(lists);
    else:
        count=0;
        for (port,passwd) in lists.items():
            if passwd[-len(status):]==status: count+=1
        return count
         
		
def del_port(config,port):
    configport=config.get('port_password');
    if configport.has_key(str(port)):
        #if configport[port][-4:]!='stop':
        #    return '0','Can not delete not stoped port! Please stop it first!'
	del configport[str(port)];
        return port,'';
    else:
        return 0,'Can not find port[%d]' % port


