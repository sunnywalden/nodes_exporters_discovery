#/bin/python
#encoding: utf-8

import os, sys
import json
import requests
import nmap
import codecs
import ConfigParser
from logbook import Logger, TimedRotatingFileHandler

BASE_DIR = os.path.abspath(os.path.join(os.getcwd(), ".."))
sys.path.append(BASE_DIR)


class NodesMetrics:
    def __init__(self):
        handler = TimedRotatingFileHandler('../logs/nodes_metrics.log')
        handler.push_application()
        self.logger = Logger(name='nodes metrics', level='info')

        self.nodes_filename, self.nodes_file_backup_name, self.exclude_file, self.url, self.query_all_ip, self.query_current_ip = self.get_conf()
        self.nodes = {}
        self.ips = {}
        self.nodes_list = []
        self.ips_list = []

    @staticmethod
    def get_conf():
        ##从配置文件获取配置
        cp = ConfigParser.ConfigParser()
        with codecs.open(os.path.join(BASE_DIR, './config/config.ini'), 'r', encoding='utf-8') as f:
            cp.readfp(f)
            nodes_filename = cp.get('file_ds', 'file_sd_filename').strip()
            nodes_file_backup_name = cp.get('file_ds', 'nodes_file_backup_name').strip()
            exclude_file = cp.get('file_ds', 'agent_exclude_file').strip()
            url = cp.get('prome', 'url').strip()
            query_all_ip = cp.get('prome', 'query_all_ip').strip()
            query_current_ip = cp.get('prome', 'query_current_ip').strip()

        return os.path.join(BASE_DIR, nodes_filename), os.path.join(BASE_DIR, nodes_file_backup_name), os.path.join(BASE_DIR, exclude_file), url, query_all_ip, query_current_ip


    #@staticmethod
    def get_ips(self, res):
        ips = []
    
        if res.status_code == 200:
            data = res.json()['data']['result']
            for metric in data:
                # print(metric)
                ip = metric['metric']['instance_ip']
                ips.append(ip)
                # print(ip)
    
        #print('All ips in prome: %s' % ips)
        #self.logger.info('All ips in prome: %s' % ips)
        return ips


        # res = requests.get(url + query_current_ip)
        #
        # current_ips = get_ips(res)


    #@staticmethod
    def get_hosts(self, file_name):
        all_ips = []
        with open(file_name, 'r') as f:
            ips = f.read()
        ip_list = ips.split('\n')
        if file_name != self.exclude_file:
            for ip in ip_list:
                if ip.strip().endswith(':9100",'):
                    nodes_str = ip.split('"')[1]
                    ip_str = nodes_str.split(':')[0]
                    #print(nodes_str)
                    all_ips.append(ip_str)
        else:
            all_ips = ip_list
        print('All nodes from file %s is: %s' % (file_name, all_ips))
        self.logger.info('All nodes from file %s is: %s' % (file_name, all_ips))
        return all_ips

    def get_nodes_discovery(self):
        new_ips = self.get_hosts(self.nodes_filename)
        nodes_hosts = list(set(new_ips))
        current_nodes = len(nodes_hosts)
        print(current_nodes)

        if current_nodes:
            self.logger.info('************************************')
            self.logger.info(
                'There are %s nodes after nodes discovery finished: %s' % \
                (current_nodes, nodes_hosts))
            self.logger.info('************************************')
        else:
            self.logger.info('************************************')
            self.logger.error(
                'There are 0 nodes founded by nodes discovery: %s')
            self.logger.info('************************************')
        all_nodes = ' '.join(nodes_hosts)
        return current_nodes, all_nodes

    def get_stop_nodes(self):
        new_ips = self.get_hosts(self.nodes_filename)
        print(len(new_ips))
    
        res = requests.get(url + query_all_ip)
        all_ips = self.get_ips(res)
        self.logger.info(all_ips)
        print('All nodes are:')
        print(all_ips)
    
        old_ips = self.get_hosts(self.exclude_file)
    
        failed_hosts = list(set(new_ips) - set(all_ips) - set(old_ips))
        stop_nodes = len(failed_hosts)
        #failed_hosts = list(set(new_ips) - set(all_ips))
        self.logger.info('************************************')
        self.logger.warning(
            'There are %s nodes stopped now' % stop_nodes)
        self.logger.info('************************************')

        return stop_nodes, failed_hosts


if __name__ == "__main__":
    url = 'https://prom.demo.com/prome/api/v1/query?'

    query_current_ip = 'query=node_virtual_type'
    # query_current_ip = 'query=avg({__name__=~"node_disk_read_time_(ms|seconds_total)",job="nodes",device=~"(dm-|sd[a-z]).*$"}) by (instance_ip)'
    # query_current_ip = 'query=node_filesystem_inode_used'
    # query_all_ip = 'query=avg(up{job=~"nodes"}) by (instance_ip)'
    query_all_ip = 'query=up{job="nodes"}'

    handler = TimedRotatingFileHandler('../logs/test.log')
    handler.push_application()
    logger = Logger(name='test')
    # self.logger.add('../logs/test.log', rotation="1 day", compression="zip")

    nodes_metrics = NodesMetrics()
    #get_lost_nodes()
    #get_lost_nodes_file()
    lost_nodes_by_discovery, failed_hosts = nodes_metrics.get_lost_nodes_discovery()













