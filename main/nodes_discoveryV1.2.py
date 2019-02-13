#!/bin/python
# encoding:utf8

import ConfigParser
# import logging
import json
import codecs
import os
import sys
import nmap
import shutil
# from loguru import logger
from logbook import Logger, TimedRotatingFileHandler
from hosts_check import HostCheck

BASE_DIR = os.path.abspath(os.path.join(os.getcwd(), ".."))
sys.path.append(BASE_DIR)


class NodesDiscovery:

    def __init__(self):
        # logging.basicConfig(level=logging.INFO,
        #                     filename='./logs/nodes_discovery.log',
        #                     datefmt='%Y/%m/%d %H:%M:%S',
        #                     format='%(asctime)s - %(name)s - %(levelname)s - %(lineno)d - %(module)s - %(message)s')
        # logger = logging.getLogger(__name__)
        handler = TimedRotatingFileHandler('../logs/nodes_discovery.log')
        handler.push_application()
        self.logger = Logger(name='nodes discovery')

        # self.logger = loggor
        self.node_hosts, self.nodes_port, self.file_sd_filename = self.get_conf()
        # self.win_nodes_port, self.node_hosts, self.nodes_port, self.file_sd_filename = self.get_conf()
        self.nodes = {}
        self.ips = {}

    @staticmethod
    def get_conf():
        ##从配置文件获取配置
        cp = ConfigParser.ConfigParser()
        with codecs.open(os.path.join(BASE_DIR, './config/config.ini'), 'r', encoding='utf-8') as f:
            cp.readfp(f)
            node_hosts = eval(cp.get('nodes', 'node_hosts').strip())
            nodes_port = int(cp.get('nodes', 'node_port').strip())
            # win_nodes_port = int(cp.get('nodes', 'windows_node_port').strip())
            file_sd_filename = cp.get('file_ds', 'file_sd_filename').strip()
        # return win_nodes_port, node_hosts, nodes_port, os.path.join(BASE_DIR, file_sd_filename)

        return node_hosts, nodes_port, os.path.join(BASE_DIR, file_sd_filename)

    def node_scaner(self, group_name, ip_range):
        port_scaner = nmap.PortScanner()
        try:
            # if group_name != 'windows':
            # 调用扫描方法，参数指定扫描主机hosts，nmap扫描命令行参数arguments
            port_scaner.scan(hosts=ip_range, arguments=' -v -sS -p ' + str(self.nodes_port))
            # else:
            #     port_scaner.scan(hosts=ip_range, arguments=' -v -sS -p ' + str(self.win_nodes_port))
        except Exception as e:
            self.logger.error("Scan erro:" + str(e))
        self.logger.info('nmap port scanner finished!')

        if group_name not in self.nodes:
            self.nodes[group_name] = []
        if group_name not in self.ips:
            self.ips[group_name] = []
        gp_name = group_name.replace('-', '_')
        for host in port_scaner.all_hosts():  # 遍历扫描主机
            self.logger.debug(port_scaner[host])
            if port_scaner[host]['status']['state'] == 'up':
                host = port_scaner[host]['addresses']['ipv4']
                try:
                    # if group_name != 'windows':
                    state = port_scaner[host]['tcp'][9100]['state']
                    # else:
                    #     state = port_scaner[host]['tcp'][9182]['state']
                except Exception as e:
                    self.logger.error('Error while get state of host %s: %s' % (host, e))
                    continue
                else:
                    self.logger.debug("Host %s %s is %s" % (str(host), str(self.nodes_port), str(state)))
                    if state == 'open':
                        # if group_name != 'windows':
                        self.nodes[group_name].append(host + ':' + str(self.nodes_port))
                        # else:
                        #     self.nodes[group_name].append(host + ':' + str(self.win_nodes_port))
                        self.ips[group_name].append(host)
                        # logger.debug('debug info of nodes: %s anf hosts: %s' % (self.nodes, self.ips))
                        self.logger.debug('debug info of nodes: [group: %s, ip: %s]' % (group_name, host))
        self.logger.info('Finished for ips %s' % ip_range)

    def host_to_file_sd(self, hosts_dict):
        hosts_conf = json.load(open(self.file_sd_filename, 'r'))

        # node_hosts = hosts_conf[0]['targets']
        # logger.info('Nodes hosts already found: %s' % node_hosts)

        self.logger.info('Latest nodes hosts: %s' % hosts_dict)

        for hosts in hosts_conf:
            if hosts['labels']['job'] == 'nodes':
                nodes_list = hosts['targets']
                self.logger.debug('Nodes before update: %s' % nodes_list)
                for group_name in hosts_dict:
                    nodes_list + hosts_dict[group_name]
                self.logger.debug('Nodes updated: %s' % nodes_list)
                nodes_all = list(set(nodes_list))
                hosts['targets'] = nodes_all


            # count = 0
            # for hosts in hosts_conf:
            #     if hosts['labels']['hosts_group'] == group_name:
            #         hosts['targets'] = hosts_dict[group_name]
            #         break
            #     else:
            #         count += 1
            # if count == len(hosts_conf):
            #     new_group = {
            #         "labels": {
            #             "job": "nodes",
            #             "hosts_group": group_name
            #         },
            #         "targets": hosts_dict[group_name]}
            #     hosts_conf.append(new_group)

        hosts_file = json.dumps(hosts_conf, indent=4, ensure_ascii=False, sort_keys=False, encoding='utf-8')
        try:
            with open(self.file_sd_filename, 'w') as f:
                f.write(hosts_file)
        except Exception as e:
            self.logger.info('Write node_exporter info failed: %s' % e)
        else:
            shutil.copy(self.file_sd_filename, '../../file_ds/nodes.json')

    def node_scan(self):
        self.logger.info('hosts groups from configure file: %s' % self.node_hosts)
        node_hosts_dict = {}

        for group_name in self.node_hosts:
            node_hosts_dict[group_name] = []
            ip_lists = self.node_hosts[group_name]
            self.logger.debug('Scan ip range %s of group %s ' % (group_name, ip_lists))
            if ip_lists:
                for ip_range in ip_lists:
                    if ip_range:
                        self.node_scaner(group_name, ip_range)

            host_check = HostCheck(group_name, self.ips[group_name])
            installed_hosts, missed_hosts = host_check.get_hosts()

            if installed_hosts:

                for host in installed_hosts:
                    # if group_name != 'windows':
                    node_hosts_dict[group_name].append(host + ':' + str(self.nodes_port))
                    # else:
                    #     node_hosts_dict[group_name].append(host + ':' + str(self.win_nodes_port))

            else:
                self.logger.error('Error! Please check log of host_check')
        if node_hosts_dict:
            self.host_to_file_sd(node_hosts_dict)
            self.logger.info('We finished here!')


if __name__ == '__main__':
    print('Nodes discovery started')
    nodes_discover = NodesDiscovery()
    nodes_discover.node_scan()
    print('Nodes discovery finished')
