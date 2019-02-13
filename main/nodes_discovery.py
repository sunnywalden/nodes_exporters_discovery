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
from get_nodes import NodesMetrics

BASE_DIR = os.path.abspath(os.path.join(os.getcwd(), ".."))
sys.path.append(BASE_DIR)


class NodesDiscovery:

    def __init__(self):
        handler = TimedRotatingFileHandler('../logs/nodes_discovery.log')
        handler.push_application()
        self.logger = Logger(name='nodes discovery', level='info')
        self.node_hosts, self.nodes_port, self.file_sd_filename, self.nodes_file_backup_name, self.exclude_file, self.metric_filename, self.metric_store_path = self.get_conf()
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
            node_hosts = eval(cp.get('nodes', 'node_hosts').strip())
            nodes_port = int(cp.get('nodes', 'node_port').strip())
            file_sd_filename = cp.get('file_ds', 'file_sd_filename').strip()
            nodes_file_backup_name = cp.get('file_ds', 'nodes_file_backup_name').strip()
            exclude_file = cp.get('file_ds', 'agent_exclude_file').strip()
            metric_filename = cp.get('prome', 'metric_filename').strip()
            metric_store_path = cp.get('prome', 'metric_store_path').strip()

        return node_hosts, nodes_port, os.path.join(BASE_DIR, file_sd_filename), os.path.join(BASE_DIR, nodes_file_backup_name), os.path.join(BASE_DIR, exclude_file), os.path.join(BASE_DIR, metric_filename), metric_store_path

    def node_scaner(self, ip_range):
        port_scaner = nmap.PortScanner()
        try:
            # 调用扫描方法，参数指定扫描主机hosts，nmap扫描命令行参数arguments
            port_scaner.scan(hosts=ip_range, arguments=' -v -sS -O -p {0} --excludefile {1}'.format(
                str(self.nodes_port), self.exclude_file), sudo=True)
        except Exception as e:
            self.logger.error("Scan erro:" + str(e))
        self.logger.info('nmap port scanner finished!')

        for host in port_scaner.all_hosts():  # 遍历扫描主机
            self.logger.debug(port_scaner[host])
            if port_scaner[host]['status']['state'] == 'up':
                host = port_scaner[host]['addresses']['ipv4']
                try:
                    nodes_state = port_scaner[host]['tcp'][9100]['state']
                except Exception as e:
                    self.logger.error('Error while get state of host %s: %s' % (host, e))
                    continue
                else:
                    self.logger.debug("Host %s %s is %s" % (str(host), str(self.nodes_port), str(nodes_state)))

                    if nodes_state == 'open':
                        os_classes = port_scaner[host]['osmatch']
                        for os_class_info in os_classes:
                            for os_family_info in os_class_info['osclass']:
                                os_family = os_family_info['osfamily']

                                self.logger.debug("Host %s system is %s" % (str(host), os_family))
                                if os_family == 'Linux':
                                    self.nodes_list.append(host + ':' + str(self.nodes_port))
                                    self.ips_list.append(host)

                                    self.logger.debug('debug info of nodes: [ip: %s]' % host)
                                    break
                            break
        self.logger.info('Finished for ips %s' % ip_range)

    def host_to_file_sd(self, hosts_list):
        hosts_conf = json.load(open(self.file_sd_filename, 'r'))

        self.logger.debug('Latest nodes hosts: %s' % hosts_list)

        for hosts in hosts_conf:
            if hosts['labels']['job'] == 'nodes':
                original_nodes_list = hosts['targets']
                self.logger.debug('Nodes before update: %s' % original_nodes_list)
                self.logger.debug('Nodes updated: %s' % hosts_list)
                # ensure_nodes = list(set(original_nodes_list) - set(hosts_list))
                # uninstall_nodes = []
                # for nodes_host in ensure_nodes:
                #     port_scaner = nmap.PortScanner()
                #     try:
                #         # 调用扫描方法，参数指定扫描主机hosts，nmap扫描命令行参数arguments
                #         port_scaner.scan(hosts=nodes_host, arguments=' -v -sS -p {0},22'.format(
                #             str(self.nodes_port)), sudo=True)
                #     except Exception as e:
                #         self.logger.error("Scan erro:" + str(e))
                #     for host in port_scaner.all_hosts():  # 遍历扫描主机
                #         self.logger.debug(port_scaner[host])
                #         if port_scaner[host]['status']['state'] == 'up':
                #             host = port_scaner[host]['addresses']['ipv4']
                #             try:
                #                 nodes_state = port_scaner[host]['tcp'][9100]['state']
                #             except Exception as e:
                #                 self.logger.error('Error while get state of host %s: %s' % (host, e))
                #                 continue
                #             else:
                #                 self.logger.debug(
                #                     "Host %s %s is %s" % (str(host), str(self.nodes_port), str(nodes_state)))
                #                 if nodes_state != 'open':
                #                     uninstall_nodes.append(host)

                nodes_all = list(set(hosts_list).union(set(original_nodes_list)))
                hosts['targets'] = nodes_all
                self.logger.info('nodes hosts file updated!')

        hosts_file = json.dumps(hosts_conf, indent=4, ensure_ascii=False, sort_keys=False, encoding='utf-8')
        try:
            with open(self.file_sd_filename, 'w') as f:
                f.write(hosts_file)
        except Exception as e:
            self.logger.error('Write node_exporter info failed: %s' % e)
        else:
            shutil.copy(self.file_sd_filename, '../../file_ds/nodes.json')

    def node_scan(self):
        self.logger.debug('hosts groups from configure file: %s' % self.node_hosts)

        for ip_range in self.node_hosts:
            self.logger.debug('Scan ip range %s' % ip_range)
            if ip_range:
                self.node_scaner(ip_range)

        if self.nodes_list:
            self.host_to_file_sd(self.nodes_list)
            self.logger.info('We finished here!')

    def nodes_file_backup(self):
        self.logger.info('Backup %s before start scanning' % self.file_sd_filename)
        shutil.copy(self.file_sd_filename, self.nodes_file_backup_name)

    def send_metrics(self):
        nodes_metrics = NodesMetrics()
        nodes_by_discovery, nodes_hosts = nodes_metrics.get_nodes_discovery()
        #nodes_type, changed_hosts = nodes_metrics.get_lost_nodes_discovery()
        current_nodes_by_discovery, lost_nodes_by_discovery, lost_nodes, new_nodes_by_discovery, new_nodes = nodes_metrics.get_lost_nodes_discovery()
        #metrics_str = 'nodes_discovery_hosts{nodes_type="' + nodes_type + '",changed_hosts="' + changed_hosts + '"} ' + str(nodes_by_discovery)
        lost_nodes_str = lost_nodes
        new_nodes_str = new_nodes
        all_nodes_metrics_str = 'nodes_discovery_hosts ' + str(current_nodes_by_discovery)
        lost_nodes_metrics_str = 'nodes_discovery_lost_hosts ' + str(lost_nodes_by_discovery)
        add_nodes_metrics_str = 'nodes_discovery_added_hosts ' + str(new_nodes_by_discovery)
        self.logger.warning('Lost nodes by discovery: %s' % lost_nodes)
        self.logger.info('New nodes by discovery: %s' % new_nodes)
        try:
            with open(self.metric_filename, 'w') as f:
                #f.write(metrics_str)
                f.write(all_nodes_metrics_str)
                f.write('\n')
                f.write(lost_nodes_metrics_str)
                f.write('\n')
                f.write(add_nodes_metrics_str)
                f.write('\n')
        except Exception as e:
            self.logger.error('Write nodes discovery metrics failed: %s' % e)
        else:
            self.logger.info('Send nodes discovery metrics : %s %s %s' % (all_nodes_metrics_str, lost_nodes_metrics_str, add_nodes_metrics_str))
            shutil.copy(self.metric_filename, os.path.join(self.metric_store_path, 'all_nodes.prom'))
        #return lost_nodes_str
        if lost_nodes_str:
            lost_nodes = lost_nodes_str.split(' ')
            nodes_discover.logger.warning('Nodes losts: %s' % lost_nodes)
            nodes_discover.host_to_file_sd(lost_nodes)


if __name__ == '__main__':
    print('Nodes discovery started')
    nodes_discover = NodesDiscovery()
    nodes_discover.nodes_file_backup()
    nodes_discover.node_scan()
    nodes_discover.send_metrics()
    print('Nodes discovery finished')
