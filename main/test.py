#/bin/python3.7
#encoding: utf-8

import json
import requests
import nmap
from loguru import logger


url = 'https://prom.ctcfin.com/prome/api/v1/query?'

query_current_ip = 'query=node_kernel'

query_all_ip = 'query=up{job="nodes"}'

logger.add('../logs/test.log', rotation="1 day", compression="zip")


def get_ips(res):
    ips = []

    if res.status_code == 200:
        data = res.json()['data']['result']
        for metric in data:
            # print(metric)
            ip = metric['metric']['instance_ip']
            ips.append(ip)
            # print(ip)

    print('All ips in prome: %s' % ips)
    logger.info('All ips in prome: %s' % ips)
    return ips


# res = requests.get(url + query_current_ip)
#
# current_ips = get_ips(res)


def get_all_hosts():
    all_ips = []
    with open('../data/hosts', 'r') as f:
        ips = f.read()
    ip_list = ips.split('\n')
    for ip in ip_list:
        if not ip.startswith('['):
            all_ips.append(ip)
    print('All ips in hosts file: %s' % all_ips)
    logger.info('All ips in hosts file: %s' % all_ips)
    return all_ips


def get_lost_nodes():
    res = requests.get(url + query_all_ip)

    ips = get_ips(res)
    all_ips = get_all_hosts()

    failed_hosts = list(set(all_ips) - set(ips))
    print('************************************')
    print(failed_hosts)
    print('************************************')
    logger.info('************************************')
    logger.info(failed_hosts)
    logger.info('************************************')


    lost_ips = []

    port_scaner = nmap.PortScanner()

    for ip in failed_hosts:
        if ip:

            try:
                port_scaner.scan(hosts=ip, arguments=' -v -sS -p ' + str(9100))
            except Exception as e:
                print("Scan erro:" + str(e))
                logger.error("Scan erro:" + str(e))
            print('nmap port scanner finished!')

            for host in port_scaner.all_hosts():  # 遍历扫描主机
                print(port_scaner[host])
                logger.debug(port_scaner[host])
                if port_scaner[host]['status']['state'] == 'up':
                    host = port_scaner[host]['addresses']['ipv4']
                    state = port_scaner[host]['tcp'][9100]['state']
                    if state == 'open':
                        lost_ips.append(host)

    print('All lost nodes are: %s' % lost_ips)
    logger.success('All lost nodes are: %s' % lost_ips)











