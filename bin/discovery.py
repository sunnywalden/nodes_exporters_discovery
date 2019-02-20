#!venv/bin/flask/bin/python
# -*- coding:utf-8 -*-

from flask import Flask
from flask import jsonify
from logbook import Logger, TimedRotatingFileHandler
import os
import sys
import time

BASE_DIR = os.path.abspath(os.path.join(os.getcwd(), ".."))
sys.path.append(BASE_DIR)

from main.nodes_discovery import NodesDiscovery

app = Flask(__name__)

handler = TimedRotatingFileHandler('../logs/lottery_server.log')
handler.push_application()
my_logger = Logger(name='Lottery Server', level=11)


@app.route('/nodes/api/v1', methods=['GET'])
def get_nodes():
    """
    Parse interface to get numbers then request the lottery funtion to get it and post the res to user.

    """
    while True:
        my_logger.info("Start nodes scan")
        nodes_discover = NodesDiscovery()

        nodes_discover.nodes_file_backup()
        try:
            nodes_discover.node_scan()
        except Exception as e:
            my_logger.error(e)
            return jsonify({'status': 'failed', 'msg': '接口返回错误 %s' % e})
        else:
            my_logger.info('Node discovery finished!')
            return jsonify({'status': 'success', 'msg': '扫描完成'})
        nodes_discover.send_metrics()

        time.sleep(7200)



