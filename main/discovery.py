#!bin/python
# encoding:utf8

import configparser
#import logging
import json
import codecs
import os
import sys
import nmap
import shutil
from loguru import logger
from main.nodes_discovery import NodesDiscovery

BASE_DIR = os.path.abspath(os.path.join(os.getcwd(), "."))
sys.path.append(BASE_DIR)

if __name__ == '__main__':
    print('Nodes discovery started')
    nodes_discover = NodesDiscovery()
    nodes_discover.node_scan()
    print('Nodes discovery finished')