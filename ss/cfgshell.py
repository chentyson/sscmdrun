#coding=utf-8
import os
#import logging
from twisted.python import log
from jsonshell import parse_json_in_str,jsondumps
import commands
import time

#verbose = 1
#logging.basicConfig(level=logging.DEBUG);


class cfgfile:

    def __init__(self):
        self.config=self.get_config();

    def get_config(self):
        try:
    	    config_path=self.find_config();
            if config_path:
                log.msg('get_config:loading config from %s' % config_path)
                with open(config_path, 'rb') as f:
    	            try:
                        try:
                            return parse_json_in_str(f.read().decode('utf8'))
                        except ValueError as e:
      		            #print('found an error in config.json: %s',  e.message)
                            log.err('found an error in config.json: %s',  e.message)
                            os.sys.exit(1);
                    finally:
    		        f.close;
    		        #print('closed');
            else:
    	        #print('can not find config file %s' % config_path)
                log.err('can not find config file %s' % config_path)
        except Exception as e:
            log.err('get_config exception.')
            log.err();
            os.sys.exit(1)
    
    def save_config(self):
        try:
            config_path=self.find_config();
            if config_path:
                log.msg('saving config to %s' % config_path)
            else:
                log.err('can not find config file,creating %s' % config_path)
               
            with open(config_path, 'wb') as f:
    	        try:
                    try: 
                        f.write(jsondumps(self.config));
                        self.backup_config(config_path);
                        return;
                    except ValueError as e:
                        #print('found an error in config.json: %s',  e.message)
                        log.err('Exceptions when write or backup config file: %s',  e.message)
                        sys.exit(1)
                finally:
    	            f.close;
                    #print('closed');
        except Exception as e:
            log.err('Exception when save_config: %s',  e.message)
            log.err();
            os.sys.exit(1)
        
    def find_config(self):
        #config_path = os.path.join(os.path.dirname(__file__),'config.json')
        config_path='/etc/shadowsocks/config.json';
        if os.path.exists(config_path):
            return config_path
    #    config_path = os.path.join(os.path.dirname(__file__), '../', 'config.json')
        print config_path
    #    if os.path.exists(config_path):
    #        return config_path
        return None
    
    def commit(self):
        return commands.getstatusoutput('/root/sscmdrun/runss');
    
    def backup_config(self,config_path):
        newpath='/root/shadowsocks.json.backup/';
        if not os.path.exists(newpath): os.makedirs(newpath)
        newpath+='config.json.' + time.strftime('%y%m%d%H%M%S');
        (s,o)=commands.getstatusoutput('cp %s %s' % (config_path,newpath ));
        if s==0:
            log.msg('Backuped %s to %s' % (config_path,newpath))
        else:
    	    log.err('Backup config file fail:%s' % o)
        return (s,o)
       
    def portpass(self):
        return self.config.get('port_password');

    #增加一个端口，正式或测试，用户允许同时在线的 ip 数，如果ip数的端口范围满了，则返回端口号是 0
    def add_new_port(self,newpass,payortest,ipnums):
        configport = self.portpass()
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

    def find_port(self,port):
        lists=self.portpass()
        if lists.has_key(port):
            return port,lists.get(port)
        for key,value in lists.items():
            if value.find(port)!=-1:
                return(key,value)
        return (0,'')
   
    def del_port(self,port):
        configport=self.portpass();
        if configport.has_key(str(port)):
            #if configport[port][-4:]!='stop':
            #    return '0','Can not delete not stoped port! Please stop it first!'
            del configport[str(port)];
            return port,'';
        else:
            #cols,rows=dbinfo.find(userinfo);
            return 0,'Can not find port[%d]' % port
     
    def clear_port(self):
        configport=self.portpass();
        configport.clear();

    def count_port(self,status):
        lists=self.portpass();
        if status=='':
            return len(lists);
        else:
            count=0;
            for (port,passwd) in lists.items():
                if passwd[-len(status):]==status: count+=1
            return count
        
#def print_exception(e):
#    global verbose
#    logging.error(e)
#    if verbose > 0:
#        import traceback
#        traceback.print_exc()

