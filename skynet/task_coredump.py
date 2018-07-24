#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
coredump 重启任务

'''

from bible.ops_tree import OpsTree
from bible.config_reader import ConfigReader
from bible.utils import set_fabric_common_env, TIMESTAMP
from fabric.network import disconnect_all
import beanstalkc
import logging

import sys
import os
import argparse
import requests
import time
import json
from fabric.api import run, settings, env, hosts, execute, quiet

OPS_TREE = OpsTree()


class task(object):
    def __init__(self, beans_ip):
        self.beanstalk = beanstalkc.Connection(
            host=beans_ip, port=11300, connect_timeout=5)

    def put(self, name, job):
        self.beanstalk.use(name)
        return self.beanstalk.put(job, delay=5)

    def get(self, name):
        self.beanstalk.watch(name)
        job = self.beanstalk.reserve()
        job.delete()
        return job.body

    def reconnect(self):
        self.beanstalk.reconnect()


def use_ops_tree(game, region):
    config = ConfigReader(game, region)
    if config.getboolean('use_ops_tree', default=False):
        return True
    else:
        return False


def remote_port_exists(port):
    with quiet():
        return run('ss -ltn | grep -w {}'.format(port)).succeeded


def remote_process_exists(process):
    pass


def remote_file_exists(filename):
    with quiet():
        return run('test -f "{}"'.format(filename)).succeeded


def remote_dir_exists(dirname):
    with quiet():
        return run('test -d "{}"'.format(dirname)).succeeded


def get_opstree(game_server):
    url = 'http://opstree.ruizhan.com/game/game_servers/{}'.format(game_server)
    try:
        r = requests.get(url)
        if 'error' in r.json().keys():
            print('not exist master server')
            ssh_ip = region = port = mixed_server = 1
        elif r.json()['status'] == 'enabled':
            ssh_ip = r.json()['ssh_ip']
            region = r.json()['region']
            port = r.json()['port']
            mixed_server = 0
        else:
            print('game server status is disable')
            ssh_ip = region = port = 1
            mixed_server = 2
    except Exception as e:
        print(e)
        pass
    return ssh_ip, region, port, mixed_server


def coredump_task(logger, ssh_ip, game_server, port):
    @hosts(ssh_ip)
    def _coredump_task():
        # 判断 port 是否存在
        try:
            if remote_port_exists(port):
                logger.info('端口存在')
                return '1'
            else:
                logger.warning('端口不存在')
        except Exception as e:
            print(e)
            return '1'

        # 判断是否存在目录
        try:
            if remote_dir_exists('/app/{}'.format(game_server)):
                logger.info('目录存在')
            else:
                return '2'
        except Exception as e:
            logger.alert(e)
            return '2'

        # 获取进程 pid
        try:
            pid = run("cat /app/{}/backend/bin/pid".format(game_server))
            logger.info('gameserver pid is {}'.format(pid))
        except Exception as e:
            logger.alert(e)
            return '3'

        # 判断是否存在 core 文件
        _result = run(
            "if [ -e /app/opbak/core.java.{} ];then echo 'yes';else echo 'no';fi".format(pid))
        # if remote_file_exists('/app/opbak/core.java.10001'):
        if _result == 'yes':
            # _datatime = run('stat /app/opbak/core.java.* | grep Modify |cut -d " " -f 2')
            # date = time.strftime("%Y-%m-%d", time.localtime())
            # if date == _datatime:
            #    print('has today core file')
            # 开始执行启动命令
            try:
                run("export JAVA_HOME=/usr/local/jdk;export LC_ALL='en_US.UTF-8';export LANG='en_US.UTF-8';sh /app/{}/backend/bin/startup.sh start".format(game_server), pty=False)
                return '4'
            except Exception as e:
                logger.alert(e)
        else:
            logger.warning('没有生成 core file')
            return '3'

    _result = execute(_coredump_task)
    if _result[ssh_ip] == '1':
        return '端口存在，未执行启动命令'
    elif _result[ssh_ip] == '2':
        return '进程目录不存在，未执行启动命令'
    elif _result[ssh_ip] == '3':
        return '未检查到 core dump 文件，未执行启动命令'
    elif _result[ssh_ip] == '4':
        return '已执行启动命令'


def send_email(game_server, data):
    import smtplib
    import datetime

    from email.mime.multipart import MIMEMultipart
    from email.mime.text import MIMEText

    # Create message container - the correct MIME type is multipart/alternative.
    sender = "report@contoso.com"
    receivers = ['tech-op@game-reign.com']
    # receivers = ['pengchao@game-reign.com']
    msg = MIMEMultipart()
    msg['Subject'] = '[Report] coredump 故障重启 {}'.format(datetime.date.today())
    msg['From'] = sender
    msg['To'] = ', '.join(receivers)

    lines = []

    lines += ["""<tr><td align="center">{}</td><td>{}</td></tr>""".format(
        game_server, data)]

    # Create the body of the message (a plain-text and an HTML version).
    html = """
<html>
    <body>
        <table border=1 cellpadding=0 cellspacing=0><tr><th colspan=3 style='background:black;color:white'>coredump 故障重启</th></tr>
        <tr style='background:#ccc;color:black'><th width=50>GameServer</th><th width=500>结果</th></tr>
        {}
        </table>
    </body>
</html>
""".format('\n'.join(lines))

    # Record the MIME types of both parts - text/plain and text/html.
    part1 = MIMEText(html, 'html')

    # Attach parts into message container.
    # According to RFC 2046, the last part of a multipart message, in this case
    # the HTML message, is best and preferred.
    msg.attach(part1)

    # Send the message via local SMTP server.
    s = smtplib.SMTP('localhost')
    # sendmail function takes 3 arguments: sender's address, recipient's address
    # and message to send - here it is sent as one string.
    s.sendmail(sender, receivers, msg.as_string())
    s.quit()


def main():
    set_fabric_common_env()
    env.eagerly_disconnect = True
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)
    # create a file handler

    handler = logging.FileHandler('task_coredump.log')
    handler.setLevel(logging.INFO)
    # create a logging format

    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    # add the handlers to the logger

    logger.addHandler(handler)
    # game_server = 'gcmob_feiliu_10001'
    beanstalk_ip = '10.6.199.35'
    async_task = task(beanstalk_ip)
    while True:
        logger.info('heartbeat')
        content = async_task.get(name='ast_webcheck_task')
        date = json.loads(content)
        game_server = date['server']
        logger.info(game_server)

        ssh_ip, region, port, mixed_server = get_opstree(game_server)
        logger.info('server staus is {}'.format(mixed_server))
        if mixed_server == 0:
            game = game_server.split('_')[0]
            logger.info('game = {}, ssh_ip = {}, region = {}, port = {}'.format(
                game, ssh_ip, region, port))

            # 读取配置
            conf = ConfigReader(game, region)
            if conf.has_option("gateway"):
                """
                配置gateway
                """
                env.gateway = conf.get("gateway")
                if conf.has_option("gateway_port"):
                    gateway_port = conf.getint("gateway_port")
                    env.gateway = '{}:{}'.format(env.gateway, gateway_port)

            # 连接机器处理 coredump 进程
            html = coredump_task(logger, ssh_ip, game_server, port)
            send_email(game_server, html)

            # 去掉 gateway
        # 消费端假死问题，强制重新连接
        async_task.reconnect()

    # 获取消息队列

    # 查询服务树，获取信息


if __name__ == "__main__":
        main()
