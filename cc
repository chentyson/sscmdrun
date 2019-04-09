netstat -anp | awk /tcp.*:\(11\|12\|13\|14\|21\|22\|23\|24\|25\|26\|31\|32\|33\|51\|52\|53\|54\)[0-3][0-9][0-9].*:[0-9]/'{split($4,ip1,":");split($5,ip2,":");print ip1[1],ip1[2],ip2[1]}' | sort -k2 -k3 -n | awk 'BEGIN{count=0} {if(aa!=$2){aa=$2;c1=0;c2=0;bb="0.0.0.0"};split($3,ip3,".");split(bb,bbip,".");if(bbip[1]!=ip3[1] && bbip[2]!=ip3[2] && bbip[3]!=ip3[3]){bb=$3;c1++};c2++;dic[aa]=c1" "c2;count++} END {for(key in dic) print key,dic[key];}' | sort -k2 -k3 -n | awk '{if($2>1 || $3 > 10) print}'
