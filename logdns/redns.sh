#!/bin/bash
file=/etc/nginx/nginx.conf
dir=/root/sscmdrun/logdns

if [ ! -f "$dir/$1.txt" ]; then
    echo $(date) 'no oldip file $dir/$1.txt found!'>>$dir/redns.log
    exit
fi
oldip=`cat $dir/$1.txt`
#echo old is $oldip

newip=`echo $2 | sed 's/\./\\\./g'`
count=`grep -w $newip $file | wc -l`
#echo count is $count
if [ $count -gt 0 ]; then
    echo $(date) 'ip('$2') count is great than 0, multiple operation~ ignore'>>$dir/redns.log
    exit
fi

#new ip to replace
sed -i 's/'$oldip'/'$2'/g' $file
#record last ip
echo $2>$dir/$1.txt
#log
echo $(date) 'replace file:'$file' that '$oldip' with '$2' for '$1>>$dir/redns.log
#echo replace $oldip with $2 for $1,done

echo $(date) 'restarting nginx...'>>$dir/redns.log
systemctl restart nginx
echo $(date) 'restarted nginx.'>>$dir/redns.log

