import json
import requests
import logging
import os, sys

BASE_DIR = os.path.abspath(os.path.join(os.getcwd(), ".."))
sys.path.append(BASE_DIR)


class HostCheck:
    def __init__(self, group_name, hosts):
        logging.basicConfig(level=logging.DEBUG,
                            filename='../logs/hosts_check.log',
                            datefmt='%Y/%m/%d %H:%M:%S',
                            format='%(asctime)s - %(name)s - %(levelname)s - %(lineno)d - %(module)s - %(message)s')
        self.logger = logging.getLogger(__name__)
        self.group_name = group_name
        self.scanned_hosts = hosts

    def get_all_hosts(self):
        all_ips = []
        with open('../data/hosts', 'r') as f:
            ips = f.read()
        ip_list = ips.split('\n')
        for ip in ip_list:
            if not ip.startswith('['):
                all_ips.append(ip)
        return all_ips

    def get_hosts(self):
        with open('../data/hosts', 'r') as f:
            ips = f.read()
        ip_list = ips.split('\n')
        try:
            index_num = ip_list.index('[' + self.group_name + ']')
        except Exception as e:
            self.logger.info('this group %s is not exist in hosts file ' % self.group_name)
            origin_ips = []
        else:

            origin_ips = ip_list[index_num+1:-1]
            if len(origin_ips) > 1:
                for ip in origin_ips:
                    if ip.startswith('['):
                        self.logger.debug('next group found in hosts file is %s' % ip)
                        index_next_group = origin_ips.index(ip)
                        self.logger.debug('index of next group %s in hosts file is %s' % (ip, index_next_group))
                        if index_next_group == 1:
                            origin_ips_final = [origin_ips[0]]
                        else:
                            self.logger.debug('ip is in range of %s and %s' %(origin_ips[1], origin_ips[index_next_group-1]))
                            origin_ips_final = origin_ips[0:index_next_group]
                        self.logger.debug('exit loop in list after group %s info found %s' % (self.group_name, origin_ips_final))
                        break
                    else:
                        if ip == origin_ips[-1]:
                            origin_ips_final = origin_ips
                            self.logger.debug('this group is the last group in host file %s' % self.group_name)
            else:
                origin_ips_final = origin_ips





        # origin_ips = []
        # for ip in ip_list:
        #     if ip.startswith('1'):
        #             origin_ips.append(ip)

        origin_ips_set = set(origin_ips_final)
        self.logger.debug(origin_ips_set)

        with open('../data/unreachble_ips.txt', 'r') as f:
            ips = f.read()
        unreachable_ips_list = ips.split('\n')
        unreachable_ips_set = set(unreachable_ips_list)

        scanned_ips_set = set(self.scanned_hosts)

        self.logger.debug(scanned_ips_set)
        installed_hosts = list(scanned_ips_set)
        #installed_hosts = list(origin_ips_set.intersection(scanned_ips_set))
        missed_ips_final = origin_ips_set - scanned_ips_set - unreachable_ips_set
        self.logger.info('hosts of group %s has node_exporter installed are: %s' % (self.group_name, installed_hosts))
        self.logger.debug('Hosts may have node_exporter installed while metric getting failed are: %s' % missed_ips_final)

        return installed_hosts, missed_ips_final
