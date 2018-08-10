#!/usr/bin/env/python
# -*- coding: utf-8 -*-

from bible.ops_tree import OpsTree
from bible.config_reader import ConfigReader
from bible.utils import set_fabric_common_env, TIMESTAMP
from fabric.network import disconnect_all
import bible.getip as getip
import datetime

from fabric.api import run, env, hosts
import argparse
import re
import requests
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

base_html = """
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="http://www.w3.org/1999/xhtml">
  <head>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta http-equiv="Content-Type" content="text/html; charset=UTF-8">
    <title>新服审计</title>
    <style>
    /* -------------------------------------
        INLINED WITH htmlemail.io/inline
    ------------------------------------- */
    /* -------------------------------------
        RESPONSIVE AND MOBILE FRIENDLY STYLES
    ------------------------------------- */
    @media only screen and (max-width: 620px) {
      table[class=body] h1 {
        font-size: 28px !important;
        margin-bottom: 10px !important;
      }
      table[class=body] p,
            table[class=body] ul,
            table[class=body] ol,
            table[class=body] td,
            table[class=body] span,
            table[class=body] a {
        font-size: 16px !important;
      }
      table[class=body] .wrapper,
            table[class=body] .article {
        padding: 10px !important;
      }
      table[class=body] .content {
        padding: 0 !important;
      }
      table[class=body] .container {
        padding: 0 !important;
        width: 100% !important;
      }
      table[class=body] .main {
        border-left-width: 0 !important;
        border-radius: 0 !important;
        border-right-width: 0 !important;
      }
      table[class=body] .btn table {
        width: 100% !important;
      }
      table[class=body] .btn a {
        width: 100% !important;
      }
      table[class=body] .img-responsive {
        height: auto !important;
        max-width: 100% !important;
        width: auto !important;
      }
    }

    /* -------------------------------------
        PRESERVE THESE STYLES IN THE HEAD
    ------------------------------------- */
    @media all {
      .ExternalClass {
        width: 100%;
      }
      .ExternalClass,
            .ExternalClass p,
            .ExternalClass span,
            .ExternalClass font,
            .ExternalClass td,
            .ExternalClass div {
        line-height: 100%;
      }
      .apple-link a {
        color: inherit !important;
        font-family: inherit !important;
        font-size: inherit !important;
        font-weight: inherit !important;
        line-height: inherit !important;
        text-decoration: none !important;
      }
      .btn-primary table td:hover {
        background-color: #34495e !important;
      }
      .btn-primary a:hover {
        background-color: #34495e !important;
        border-color: #34495e !important;
      }
    }
    </style>
  </head>
  <body class="" style="background-color: #f6f6f6; font-family: sans-serif; -webkit-font-smoothing: antialiased; font-size: 14px; line-height: 1.4; margin: 0; padding: 0; -ms-text-size-adjust: 100%; -webkit-text-size-adjust: 100%;">
    <table border="0" cellpadding="0" cellspacing="0" class="body" style="border-collapse: separate; mso-table-lspace: 0pt; mso-table-rspace: 0pt; width: 100%; background-color: #f6f6f6;">
      <tr>
        <td style="font-family: sans-serif; font-size: 14px; vertical-align: top;">&nbsp;</td>
        <td class="container" style="font-family: sans-serif; font-size: 14px; vertical-align: top; display: block; Margin: 0 auto; max-width: 1400px; padding: 10px; width: 1300px;">
          <div class="content" style="box-sizing: border-box; display: block; Margin: 0 auto; padding: 10px;">

            <!-- START CENTERED WHITE CONTAINER -->
            <span class="preheader" style="color: transparent; display: none; height: 0; max-height: 0; max-width: 0; opacity: 0; overflow: hidden; mso-hide: all; visibility: hidden; width: 0;">This is preheader text. Some clients will show this text as a preview.</span>
            <table class="main" style="border-collapse: separate; mso-table-lspace: 0pt; mso-table-rspace: 0pt; width: 100%; background: #232322; border-radius: 3px;">

              <!-- START MAIN CONTENT AREA -->
              <tr>
                <td class="wrapper" style="font-family: sans-serif; font-size: 14px; vertical-align: top; box-sizing: border-box; padding: 20px;">
                  <table border="0" cellpadding="0" cellspacing="0" style="border-collapse: separate; mso-table-lspace: 0pt; mso-table-rspace: 0pt; width: 100%;">
                    <!-- title 模块 -->
                    <tr>
                      <td style="font-family: sans-serif; font-size: 14px; vertical-align: top;">
                        <p style="font-family: sans-serif; font-size: 14px; font-weight: normal; margin: 0; Margin-bottom: 0px; font-size: 200%; color: #ffffff">新服审计</p>
                      </td>
                    </tr>
                  </table>
"""

date_html = """
                  <table cellspacing="1" cellpadding="1" border="0">
                    <tr>
                      <td style="font-family: sans-serif; font-size: 14px; vertical-align: top;">
                        <p style="font-family: sans-serif; font-size: 14px; font-weight: normal; margin: 0; Margin-bottom: 30px; font-size: 90%; color: white; padding-bottom:1px;">{0}</p>
                      </td>
                    </tr>
                  </table>
"""

title_html_green = """
                  <table cellspacing="1" cellpadding="1" border="0">
                    <tr>
                      <td style="font-family: sans-serif; font-size: 14px; vertical-align: top;">
                        <p style="font-family: sans-serif; font-size: 14px; font-weight: normal; margin: 0; Margin-bottom: 20px; font-size: 100%; color: #2EF6F3; padding-bottom:1px;">服务树&开服列表&游戏服 完全匹配</p>
                      </td>
                    </tr>
                  </table>
"""

title_html_red = """
                  <table cellspacing="1" cellpadding="1" border="0">
                    <tr>
                      <td style="font-family: sans-serif; font-size: 14px; vertical-align: top;">
                        <p style="font-family: sans-serif; font-size: 14px; font-weight: normal; margin: 0; Margin-bottom: 20px; font-size: 100%; color: #F6261F; padding-bottom:1px;">服务树&开服列表&游戏服  {} 匹配异常</p>
                      </td>
                    </tr>
                  </table>
"""

game_html = """
<table cellspacing="3" cellpadding="3" border="0">
                    <tr>
                      <td style="font-family: sans-serif; font-size: 14px; vertical-align: top;">
                        <p style="font-family: sans-serif; font-size: 14px; font-weight: normal; margin: 0; Margin-bottom: 5px; font-size: 120%; color: white; padding-bottom:1px; border-bottom:2px solid #3199A4">{0}</p>
                      </td>
                    </tr>
                  </table>
"""

context_html = """
<table cellspacing="0" cellpadding="6" border="0">
                    <tr>
                      <th style="width: 350px; font-weight: bold; font-size: 80%; color: white; border: 1px solid #24737B;">参数</th>
                      <th style="width: 100px; font-weight: bold; font-size: 80%; color: white; border: 1px solid #24737B;">开服列表</th>
                      <th style="width: 100px; font-weight: bold; font-size: 80%; color: white; border: 1px solid #24737B;">服务树</th>
                      <th style="width: 100px; font-weight: bold; font-size: 80%; color: white; border: 1px solid #24737B;">游戏服</th>
                    </tr>
                    <tr>
                      <td style="width: 350px; font-weight: bold; text-align: center; font-size: 80%; color: white; border: 1px solid #24737B;">{0}</td>
                      <td style="width: 100px; font-weight: bold; text-align: center; font-size: 80%; color: white; border: 1px solid #24737B;">●</td>
                      <td style="width: 100px; font-weight: bold; text-align: center; font-size: 80%; color: white; border: 1px solid #24737B;">{1}</td>
                      <td style="width: 100px; font-weight: bold; text-align: center; font-size: 80%; color: white; border: 1px solid #24737B;">{2}</td>
                    </tr>
                    <tr>
                      <td style="width: 350px; font-weight: bold; text-align: center; font-size: 80%; color: white; border: 1px solid #24737B;">Host: {3}</td>
                      <td style="width: 100px; font-weight: bold; text-align: center; font-size: 80%; color: white; border: 1px solid #24737B;">●</td>
                      <td style="width: 100px; font-weight: bold; text-align: center; font-size: 80%; color: white; border: 1px solid #24737B;">{4}</td>
                      <td style="width: 100px; font-weight: bold; text-align: center; font-size: 80%; color: white; border: 1px solid #24737B;">{5}</td>
                    </tr>
                    <tr>
                      <td style="width: 350px; font-weight: bold; text-align: center; font-size: 80%; color: white; border: 1px solid #24737B;">IP: {6}</td>
                      <td style="width: 100px; font-weight: bold; text-align: center; font-size: 80%; color: white; border: 1px solid #24737B;">●</td>
                      <td style="width: 100px; font-weight: bold; text-align: center; font-size: 80%; color: white; border: 1px solid #24737B;">{7}</td>
                      <td style="width: 100px; font-weight: bold; text-align: center; font-size: 80%; color: white; border: 1px solid #24737B;">{8}</td>
                    </tr>
                    <tr>
                      <td style="width: 350px; font-weight: bold; text-align: center; font-size: 80%; color: white; border: 1px solid #24737B;">Port: {9}</td>
                      <td style="width: 100px; font-weight: bold; text-align: center; font-size: 80%; color: white; border: 1px solid #24737B;">●</td>
                      <td style="width: 100px; font-weight: bold; text-align: center; font-size: 80%; color: white; border: 1px solid #24737B;">{10}</td>
                      <td style="width: 100px; font-weight: bold; text-align: center; font-size: 80%; color: white; border: 1px solid #24737B;">{11}</td>
                    </tr>
                    <tr>
                      <td style="width: 350px; font-weight: bold; text-align: center; font-size: 80%; color: white; border: 1px solid #24737B;">开服时间：{12}</td>
                      <td style="width: 100px; font-weight: bold; text-align: center; font-size: 80%; color: white; border: 1px solid #24737B;">●</td>
                      <td style="width: 100px; font-weight: bold; text-align: center; font-size: 80%; color: white; border: 1px solid #24737B;">{13}</td>
                      <td style="width: 100px; font-weight: bold; text-align: center; font-size: 80%; color: white; border: 1px solid #24737B;">{14}</td>
                    </tr>
                  </table>
"""

end_html = """
</td>
              </tr>

            <!-- END MAIN CONTENT AREA -->
            </table>

            <!-- START FOOTER -->
   <!--          <div class="footer" style="clear: both; Margin-top: 10px; text-align: center; width: 100%;">
              <table border="0" cellpadding="0" cellspacing="0" style="border-collapse: separate; mso-table-lspace: 0pt; mso-table-rspace: 0pt; width: 100%;">
                <tr>
                  <td class="content-block" style="font-family: sans-serif; vertical-align: top; padding-bottom: 10px; padding-top: 10px; font-size: 12px; color: #999999; text-align: center;">
                    <span class="apple-link" style="color: #999999; font-size: 12px; text-align: center;">Company Inc, 3 Abbey Road, San Francisco CA 94102</span>
                    <br> Don't like these emails? <a href="http://i.imgur.com/CScmqnj.gif" style="text-decoration: underline; color: #999999; font-size: 12px; text-align: center;">Unsubscribe</a>.
                  </td>
                </tr>
                <tr>
                  <td class="content-block powered-by" style="font-family: sans-serif; vertical-align: top; padding-bottom: 10px; padding-top: 10px; font-size: 12px; color: #999999; text-align: center;">
                    Powered by <a href="http://htmlemail.io" style="color: #999999; font-size: 12px; text-align: center; text-decoration: none;">HTMLemail</a>.
                  </td>
                </tr>
              </table>
            </div> -->
            <!-- END FOOTER -->

          <!-- END CENTERED WHITE CONTAINER -->
          </div>
        </td>
        <td style="font-family: sans-serif; font-size: 14px; vertical-align: top;">&nbsp;</td>
      </tr>
    </table>
  </body>
</html>
"""

def get_opstree(game_server):
    url = 'http://opstree.ruizhan.com/game/game_servers/{}'.format(game_server)
    try:
        r = requests.get(url)
        if 'error' in r.json().keys():
            print('not exist master server')
            ssh_ip = region = port = mixed_server = 1
        elif r.json()['status'] == 'enabled':
            dns = r.json()['dns']
            ssh_ip = r.json()['ssh_ip']
            name = r.json()['name']
            port = r.json()['port']
            open_time = r.json()['open_time']
    except Exception as e:
        pass
    return dns, ssh_ip, name, port, open_time

def get_pubip(ssh_ip):
    ''' 获取公网 ip'''
    env.host_string = ssh_ip
    wip = run("curl -s ipip.aoshitang.com | sed 's/[^0-9\\.]*\\(.*\\)/\\1/g'", quiet=True)
    return(wip)

def diff_gameserver(server_game, server_name, server_port, server_dns, server_opentime, server_ip):
    '''开服列表和游戏服对比
    '''
    if server_game == 'tjxs':
        server_name = server_name.replace('37', '37wan')
    if server_game == 'gcld':
        server_name = server_name.replace('feiliuapp', 'feiliu')
        if re.compile('feiliu').match(server_name):
            server_name = 'gcmob_feiliu_{}'.format(server_name.split('feiliu')[1])
        if re.compile('maingames').match(server_name):
            server_name = 'gcmob_maingames_{}'.format(server_name.split('_')[1])
        if re.compile('coco').match(server_name):
            server_name = 'gcmob_coco_{}'.format(server_name.split('coco')[1])
        if re.compile('ujoy').match(server_name):
            server_name = 'gcmob_ujoy_{}'.format(server_name.split('ujoy')[1])
        if re.compile('changicth').match(server_name):
            server_name = 'gcmob_thailand_{}'.format(server_name.split('changicth')[1])
        if re.compile('qianqi').match(server_name):
            server_name = 'gcmob_qianqi_{}'.format(server_name.split('qianqi')[1])
    ops_dns, ops_sship, ops_name, ops_port, ops_opentime = get_opstree(server_name)
    gameserver_wip = get_pubip(ops_sship)
    env.host_string = ops_sship
    gameserver_name = run('if [ -d /app/{} ];then echo "yes"; else echo "no"; fi'.format(ops_name), quiet=True)
    print(gameserver_name)

def diff_ops(server_game, server_name, server_port, server_dns, server_opentime, server_ip):
    '''
    开服列表和服务树对比
    '''
    server_http = server_dns.replace('http://', '').replace('/root/', '')
    if server_game == 'tjxs':
        server_name = server_name.replace('37', '37wan')
    if server_game == 'gcld':
        server_name = server_name.replace('feiliuapp', 'feiliu')
        if re.compile('feiliu').match(server_name):
            server_name = 'gcmob_feiliu_{}'.format(server_name.split('feiliu')[1])
        if re.compile('maingames').match(server_name):
            server_name = 'gcmob_maingames_{}'.format(server_name.split('_')[1])
        if re.compile('coco').match(server_name):
            server_name = 'gcmob_coco_{}'.format(server_name.split('coco')[1])
        if re.compile('ujoy').match(server_name):
            server_name = 'gcmob_ujoy_{}'.format(server_name.split('ujoy')[1])
        if re.compile('changicth').match(server_name):
            server_name = 'gcmob_thailand_{}'.format(server_name.split('changicth')[1])
        if re.compile('qianqi').match(server_name):
            server_name = 'gcmob_qianqi_{}'.format(server_name.split('qianqi')[1])
    ops_dns, ops_sship, ops_name, ops_port, ops_opentime = get_opstree(server_name)
    ops_wip = get_pubip(ops_sship)
    server_name_id = server_http_id = server_ip_id = server_port_id = server_opentime_id = 1
    if server_name == ops_name:
        ops_name_id = server_name_id
    else:
        ops_name_id = server_name_id + 1
    if server_http == ops_dns:
        ops_dns_id = server_name_id
    else:
        ops_dns_id = server_name_id + 1
    if server_ip == ops_wip:
        ops_wip_id = server_ip_id
    else:
        ops_wip_id = server_ip_id + 1
    if server_port == str(ops_port):
        ops_port_id = server_port_id
    else:
        ops_port_id = server_port_id + 1
    if server_opentime.split(' ')[0] == ops_opentime.split(' ')[0]:
        ops_opentime_id = server_opentime_id
    else:
        ops_opentime_id = server_opentime_id + 1
    return ops_name_id, ops_dns_id, ops_wip_id, ops_port_id, ops_opentime_id

def deal_sql(sql):
    serverinfo = []
    # print(sql.split('|')[1:-1])
    sqllist = sql.split('|')[1:-1]
    # serverinfo.append(sqllist[i: i+4] for i in range(0, 4))
    # print(len(sqllist))
    for i in range(0, len(sqllist), 8):
        # print(sqllist[i:i+8])
        serverinfo.append(sqllist[i:i+8])
    # print(serverinfo)
    return serverinfo

def server_info():
    '''
    从开服列表获取最近新服
    '''
    memp_ip = '10.6.199.16'
    mlist_ip = '10.6.197.224'
    # 获取 memp 平台新服信息
    env.host_string = memp_ip
    memp_comming_soon = run('''pandora reign_moblist -N -e "select game_id, game_name,host,ip,port,server_id,online_date from ios_server where status = '即将开启' and online_date <= DATE_ADD(CURDATE(), INTERVAL 2 DAY)"''', quiet=True)
    memp_now = run('''pandora reign_moblist -N -e "select game_id, game_name, host, ip, port, server_id, online_date from ios_server where status = '推荐' and date(online_date) = CURDATE()"''', quiet=True)
    # now = run('''pandora reign_moblist -N -e "select game_id, game_name, host, ip, port, server_id, online_date from ios_server where status = '推荐1' and date(online_date) = CURDATE()"''', quiet=True)
     # deal_sql(comming_soon)
     # deal_sql(now)
    memp_list = deal_sql(memp_comming_soon) + deal_sql(memp_now)

    # 获取 mlist 平台新服信息
    env.host_string = mlist_ip
    mlist_comming_soon = run('''pandora reign_moblist_1 -N -e "select game_id, game_name,host,ip,port,server_id,online_date from ios_server where status = '即将开启' and online_date <= DATE_ADD(CURDATE(), INTERVAL 2 DAY)"''', quiet=True)
    mlist_now = run('''pandora reign_moblist_1 -N -e "select game_id, game_name, host, ip, port, server_id, online_date from ios_server where status = '推荐' and date(online_date) = CURDATE()"''', quiet=True)
    mlist_list = deal_sql(mlist_comming_soon) + deal_sql(mlist_now)
    # print("memp list is {}".format(memp_list))
    # print("memp list is {}".format(mlist_list))
    return memp_list + mlist_list

def send_mail(html):
    sender = "report@contoso.com"
    receivers = ['pengchao@game-reign.com']
    # receivers = ['tech-op@game-reign.com']
    msg = MIMEMultipart()
    msg['Subject'] = '[新服审计] {}'.format(datetime.date.today())
    msg['From'] = sender
    msg['To'] = ', '.join(receivers)
    part = MIMEText(html, 'html')
    msg.attach(part)
    s = smtplib.SMTP('localhost')
    s.sendmail(sender, receivers, msg.as_string())
    s.quit()


def audit_new(args):
    '''
    新服三方校验
    '''
    game = args.game
    # region = args.region
    # conf = ConfigReader(game, region)
    # 获取今日推荐和明日新服信息
    serverlist = server_info()
    # print(serverlist)
    # 异常服
    abnormal_server_list = []
    today = datetime.datetime.now().strftime("%Y-%m-%d")
    html_total = base_html + '\n'
    html_total += date_html.format(today)
    html_total += '\n'
    html_total += title_html_green
    html_total += '\n'

    for i in serverlist:
        server_game = i[0].strip()
        server_name = i[5].strip()
        server_port = i[4].strip()
        server_dns = i[2].strip()
        server_http = server_dns.replace('http://', '').replace('/root/', '')
        server_opentime = i[6].strip()
        server_ip = i[3].strip()
        ops_name_id, ops_dns_id, ops_wip_id, ops_port_id, ops_opentime_id = diff_ops(server_game, server_name, server_port, server_dns, server_opentime, server_ip)
        gameserver_name_id, gameserver_dns_id, gameserver_ip_id, gameserver_port_id, gameserver_opentime_id = ops_name_id, ops_dns_id, ops_wip_id, ops_port_id, ops_opentime_id
        if ops_name_id + ops_dns_id + ops_wip_id + ops_port_id + ops_opentime_id == 5:
            pass
        else:
            abnormal_server_list.append(server_name)

        if server_game == 'tjxs':
            server_game = 'tjmob'
        html_total += game_html.format(server_game)
        html_total += '\n'
        if ops_name_id == 1:
            ops_name_html = '●'
        else:
            ops_name_html = '○'
        if ops_dns_id == 1:
            ops_dns_html = '●'
        else:
            ops_dns_html = '○'

        if ops_wip_id == 1:
            ops_wip_html = '●'
        else:
            ops_wip_html = '○'
        if ops_port_id == 1:
            ops_port_html = '●'
        else:
            ops_port_html = '○'
        if ops_opentime_id == 1:
            ops_opentime_html = '●'
        else:
            ops_opentime_html = '○'
        gameserver_name_html, gameserver_dns_html, gameserver_ip_html, gameserver_port_html, gameserver_opentime_html = ops_name_html, ops_dns_html, ops_wip_html, ops_port_html, ops_opentime_html
        html_total += '\n'
        html_total += context_html.format(server_name, ops_name_html, gameserver_name_html, server_http, ops_dns_html, gameserver_dns_html, server_ip, ops_wip_html, gameserver_ip_html, server_port, ops_port_html, gameserver_port_html, server_opentime, ops_opentime_html, gameserver_opentime_html)
        html_total += '\n'
    html_total += end_html
    return html_total

        # diff_gameserver(server_game, server_name, server_port, server_dns, server_opentime, server_ip)
    #print('----')
    #print(comming_soon)
    #print('----')
    #print(now)


def main():
    set_fabric_common_env()
    env.eagerly_disconnect = True
    parser = argparse.ArgumentParser(
            description='每日审计新服,并发送报告.'
            )
    parser.add_argument(
            '-g',
            dest='game',
            help='game; eg: gcmob'
            )
    args = parser.parse_args()
    html_all = audit_new(args)
    send_mail(html_all)



if __name__ == "__main__":
    main()
