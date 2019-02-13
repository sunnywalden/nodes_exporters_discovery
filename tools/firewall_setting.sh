#!/bin/bash

#check the release of system
CENTOS_SERIES=`egrep 'CentOS|Redhat|Red\ Hat' /etc/redhat-release|wc -l`
SYSTEM_BITS_CHECK=`uname -a|grep x86_64|wc -l`
SYSTEM_VERSION_CHECK=`egrep ' 7\.' /etc/redhat-release |wc -l`
SYSTEM_VERSION6_CHECK=`egrep ' 6\.' /etc/redhat-release |wc -l`
SYSTEM_VERSION5_CHECK=`egrep ' 5\.' /etc/redhat-release |wc -l`
nodeexporter_port=9100

check_version() {
  if [ $CENTOS_SERIES -eq 1 -a $SYSTEM_VERSION_CHECK -eq 1 ];then
    #echo "system version is ceontos 7"
    sys_release='centos7'
  elif [ $CENTOS_SERIES -eq 1 -a $SYSTEM_VERSION6_CHECK -eq 1 ];then
    #echo "system version is ceontos 6"
    sys_release='centos6'
  elif [ $CENTOS_SERIES -eq 1 -a $SYSTEM_VERSION5_CHECK -eq 1 ];then
    #echo "system version is ceontos 5"
    sys_release='centos5'
  else
    #echo "system version is not centos"
    return 0
  fi
}

check_version
if [ $sys_release == "centos7" ];then
  check_iptable=`service iptables status|grep -v inactive|grep active|grep -v grep|wc -l`
else
  check_iptable=`service iptables status|egrep '1|running' |grep -v grep|wc -l`
fi
if [ $check_iptable -ne 0 ];then
  check_iptables_setting=`iptables -L -n |grep $nodeexporter_port|grep -v grep|wc -l`
  if [ $check_iptables_setting -eq 0 ];then
    iptables -A INPUT -p tcp --dport $nodeexporter_port -j ACCEPT
    service iptables save
  fi
fi
echo 'firewall setting finished!'
