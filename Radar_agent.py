#!/use/bin/env python
# -*- coding:utf-8 -*-

'''
    Radar agnet：
        1、zabbix server 端从 redis 中采集告警信息，进行聚合；
        2、推送到 Radar server 中；
        3、采集频率由 cron 控制；

    2018-03-19 init Pengch
'''

import redis
import os, sys, re
import smtplib
import datetime

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

ALERT_LEVEL = {'P0':['Disk dmesg error on', 'MySQL is down on', 'is Down', 'Disk Read-only on'],
               'P1':['has deadlock on', 'MySQL has just been restarted', 'has just been restarted'],
               'P2':['JAVA.rsp_time is over', 'BLOCKED is over 20 on', 'webcheck is warning on', 'JAVA.CPU.Usage is over', 'gameport is warning on', 'web.test.fail is warning on']}

ALERT_LEVEL_USE = {'Disk +dmesg +error':'P0', 'MySQL +is +down':'P0', 'is +DOWN':'P0', 'Disk +Read-only':'P0',
                'has +deadlock':'P1', 'MySQL +has +just +been +restarted':'P1', 'has +just +been +restarted':'P1',
                'BLOCKED +is +over +20 +on':'P2', 'webcheck +is +warning':'P2',  'gameport +is +warning':'P2',
                'web.test.fail +is +warning +on':'P2', 'MySQL +QPS +is +over': 'P2',
                'JAVA.OldGC +is +over +%92': 'P2', 'serviceport +is +warning': 'P2'}

ALERT_LEVEL_EXP = {'JAVA.rsp_time +is +over':'P2', 'JAVA.CPU.Usage +is +over':'P2', 'MySQL +CPU +Usage +is +over': 'P2', 'Processor +load +is +high': 'P2',
                   'Ping +response +time +is +over +200ms': 'P2', 'Offset +over +30 +second': 'P2', 'Free +disk +space +is +less +than +10%': 'P2',
                   'Free +disk +space +is +less +than +15%': 'P3', 'Disk +I/O +is +overloaded': 'P2',  'Network +incoming +traffic +is +over +200M': 'P2',
                   'Network +outcoming +traffic +is +over +200M': 'P2'}

class alert(object):
    '''
    The goal of this class is to modult a typeical alert and make easy to deal with alert
    '''

    def __init__(self):
        self.alertlist = []
        for i in ALERT_LEVEL.values():
            self.alertlist += i
        '''
        html data structure：
        mergeproblem = {
            P0 :
                {'JAVA.rsp_time is over' :
                    { 'sum' : 1, 'hostname': {'gcld_gcld_1': 1}, 'lastime': '23:24:44', 'status': '已恢复',
                    'norestore': {'gcld_gcld_2': 1}}, 'category': 'USE'
                },
            }
        '''
        self.mergeproblem = {}

    def sort(self, problem, resove):
        '''
        Classify alert...


        problem data structure:
        {level}#{alertname}#{category}#{hostname}#{time}#{status}

        '''

        def _level(item):
            # 过滤告警等级
            for i in ALERT_LEVEL_USE.keys():
                a = re.compile(i)
                if a.search(item):
                    result = ALERT_LEVEL_USE[i] + '#' + a.findall(item)[0] + '#USE'
                    return result

            for i in ALERT_LEVEL_EXP.keys():
                a = re.compile(i)
                if a.search(item):
                    result = ALERT_LEVEL_EXP[i] + '#' + a.findall(item)[0] + '#EXP'
                    return result

        def _getserver(item):
            # 提取出游戏服名
            try:
                a = re.compile('(\D+_\w+_\w+\.\w+|\D+_\w+_\w+)')
                # print(a.findall(item)[0])
                return a.findall(item)[0]
            except Exception as e:
                return 'no'

        def _init(item):
            # 初始化字典
            segment = []
            if type(item) is dict:
                item['P1'] = segment
                item['P2'] = segment
                item['P3'] = segment
                item['P4'] = segment
                return item
            else:
                print('no')

        # 结果字典，html 根据字典生成
        # print(_init(self.mergeproblem))

        alerts = []
        for i in problem.keys():
            problemName = problem[i].split('#')[0]
            problemHost = problem[i].split('#')[1]
            problemInfo = problem[i].split('#')[2]
            problemTime = problem[i].split('#')[3]
            problemDate = problem[i].split('#')[4]
            # print('Name: %s\nHost: %s\nInfo: %s\nTime: %s\nDate: %s' % (problemName, problemHost, problemInfo, problemTime, problemDate))
            problemLevel = _level(problemName)
            if problemLevel is None:
                problemLevel = 'Other' + '#' + problemName + '#OTH'
            problemServer = _getserver(problemName)
            if problemServer == 'no':
                problemServer = problemHost
            # 添加告警
            # print(problemLevel)
            # print(problemServer)
            # print(problemLevel + '#' + problemServer + '#' + problemTime)
            proNoStatus = problemLevel + '#' + problemServer + '#' + problemTime
            if resovelist.has_key(i):
                problemStatus = proNoStatus + '#已恢复'
            else:
                problemStatus = proNoStatus + '#未恢复'
            alerts.append(problemStatus)
        return alerts

    def compress(self, problemlist):
        '''
        压缩告警，并取最后时间
        :param problemlist:
        :return:
        '''

        def _init(alertname, hostname, lastime, status, category):
            first_dict = {}
            second_dict = {}
            third_dict = {}
            third_dict[hostname] = 1
            second_dict['sum'] = 1
            second_dict['hostname'] = third_dict
            second_dict['lastime'] = lastime
            second_dict['status'] = status
            second_dict['category'] = category
            if status == '未恢复':
                second_dict['norestore'] = third_dict
            else:
                second_dict.setdefault('norestore')
            first_dict[alertname] = second_dict
            return first_dict


        for i in problemlist:
            level = i.split('#')[0]
            alertname = i.split('#')[1]
            category = i.split('#')[2]
            hostname = i.split('#')[3]
            time = i.split('#')[4]
            status = i.split('#')[5]
            if self.mergeproblem.has_key(level):
                if self.mergeproblem[level].has_key(alertname):
                    self.mergeproblem[level][alertname]['sum'] += 1
                    if self.mergeproblem[level][alertname]['hostname'].has_key(hostname):
                        self.mergeproblem[level][alertname]['hostname'][hostname] += 1
                    else:
                        self.mergeproblem[level][alertname]['hostname'][hostname] = 1
                else:
                    temp_dict = {}
                    temp_dict['sum'] = 1
                    temp_dict['hostname'] = {hostname: 1}
                    temp_dict['lastime'] = time
                    temp_dict['status'] = status
                    temp_dict['category'] = category
                    if status == '未恢复':
                        temp_dict['norestore'] = {hostname: 1}
                    else:
                        temp_dict.setdefault('norestore')
                    self.mergeproblem[level][alertname] = temp_dict
                    # self.mergeproblem[level][alertname]['sum'] = 1
                    # self.mergeproblem[level][alertname]['hostname'] = {hostname: 1}
                    # self.mergeproblem[level][alertname]['lastime'] = time
                    # self.mergeproblem[level][alertname]['status'] = status
                    if status == '未恢复':
                        if self.mergeproblem[level][alertname]['norestore'].has_key(hostname):
                            self.mergeproblem[level][alertname]['norestore'][hostname] += 1
                        else:
                            self.mergeproblem[level][alertname]['norestore'][hostname] = 1
            else:
                self.mergeproblem[level] = _init(alertname, hostname, time, status, category)

        return self.mergeproblem

    def get(self, subject):
        '''
        get information of subjects.
        :return:
        '''
        pass

    def get_all(self):
        '''
        get all of alert now...
        :return:
        '''
        pass

def send_mail(html):
    sender = "report@contoso.com"
    receivers = ['pengchao@game-reign.com']
    msg = MIMEMultipart()
    msg['Subject'] = '[Report] 告警上报 {}'.format(datetime.date.today())
    msg['From'] = sender
    msg['To'] = ', '.join(receivers)
    part = MIMEText(html, 'html')
    msg.attach(part)
    s = smtplib.SMTP('localhost')
    s.sendmail(sender, receivers, msg.as_string())
    s.quit()

def init_hosts(hostlist):
    line = ''
    if len(hostlist) > 5:
        while len(line) == 5:
            maxitem = max(hostlist.items(), key=lambda x: x[1])[0]
            line += str(maxitem) + str(hostlist[maxitem]) + ' 次<br>'
            hostlist.pop(maxitem)
        return line
    else:
        for i in hostlist:
            line += str(i) + ' ' + str(hostlist[i]) + ' 次<br>'
        return line


def init_html(alertlist):

    def _count(alertlist, type, status):
        '''
        统计可用性，体验性次数
        :param alertlist, type, status:
        :return:
        '''
        count = 0
        for i in alertlist:
            for j in alertlist[i]:
                if alertlist[i][j]['category'] == type and alertlist[i][j]['status'] == status:
                    count += 1
        return count


    html = """
    <!doctype html>
<html>
  <head>
    <meta name="viewport" content="width=device-width">
    <meta http-equiv="Content-Type" content="text/html; charset=UTF-8">
    <title>告警上报</title>
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
            <table class="main" style="border-collapse: separate; mso-table-lspace: 0pt; mso-table-rspace: 0pt; width: 100%; background: #ffffff; border-radius: 3px;">

              <!-- START MAIN CONTENT AREA -->
              <tr>
                <td class="wrapper" style="font-family: sans-serif; font-size: 14px; vertical-align: top; box-sizing: border-box; padding: 20px;">
                  <table border="0" cellpadding="0" cellspacing="0" style="border-collapse: separate; mso-table-lspace: 0pt; mso-table-rspace: 0pt; width: 100%;">
                    <tr>
                      <td style="font-family: sans-serif; font-size: 14px; vertical-align: top;">
                        <p style="font-family: sans-serif; font-size: 14px; font-weight: normal; margin: 0; Margin-bottom: 15px; font-size: 200%; color: red;">未恢复告警</p>
                        <table border="1" cellspacing="0" cellpadding="0" style="Margin-bottom:50px;">
                           <tr style='background:#ccc;color:black;'>
                              <th width=100>类别</th>
                              <th width=50>Level</th>
                              <th width=300>告警</th>
                              <th width=300>主机</th>
                              <th width=150>最后发生时间</th>
                              <th width=100>状态</th></tr>
"""
    html2 = """
                        </table>
                        <p style="font-family: sans-serif; font-size: 14px; font-weight: normal; margin: 0; Margin-bottom: 15px; font-size: 150%;">已恢复告警</p>
                        <table border="1" cellspacing="0" cellpadding="0" style="border: 1; cellpadding: 0; cellspacing: 0; Margin-bottom: 15px;">
                          <tr style='background:#ccc;color:black;'>
                              <th width=100>类别</th>
                              <th width=50>Level</th>
                              <th width=300>告警</th>
                              <th width=300>主机</th>
                              <th width=150>最后发生时间</th>
                              <th width=100>状态</th></tr>
            """
    html3 = """
                        </table>
                      </td>
                    </tr>
                  </table>
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

    lines_restore_USE = []
    lines_restore_EXP = []
    lines_restore_OTH = []
    lines_norestore_USE = []
    lines_norestore_EXP = []
    lines_norestore_OTH = []
    category_count_USE_yes = 0
    category_count_EXP_yes = 0
    category_count_OTH_yes = 0
    category_count_USE_no = 0
    category_count_EXP_no = 0
    category_count_OTH_no = 0
    for i in alertlist.keys():
        if i == 'P3':
            for j in alertlist[i]:
                if alertlist[i][j]['norestore'] is None:
                    lines_restore_USE += ["""<tr><td align="center">{}</td><td align="center">{} {} 次</td><td align="center">{} 次</td><td align="center">{}</td><td align="center">{}</td></tr>""".format(
                        i, j, alertlist[i][j]['sum'], alertlist[i][j]['sum'], alertlist[i][j]['lastime'], alertlist[i][j]['status'])]
                else:
                    lines_restore_USE += [
                        """<tr><td align="center">{}</td><td align="center">{} {} 次</td><td align="center">{} 次</td><td align="center">{}</td><td align="center">{} 未恢复</td></tr>""".format(
                            i, j, alertlist[i][j]['sum'], alertlist[i][j]['sum'], alertlist[i][j]['lastime'],
                            alertlist[i][j]['norestore'].keys()[0])]
        else:
            for j in alertlist[i]:
                # restore_num = _count(alertlist, 'USE', '已恢复')
                # nostore_num = _count(alertlist, 'USE', '未恢复')
                hostlist = init_hosts(alertlist[i][j]['hostname'])
                if alertlist[i][j]['status'] == '未恢复':
                    if alertlist[i][j]['category'] == 'USE':
                        nostore_num = _count(alertlist, 'USE', '未恢复')
                        if category_count_USE_no == 0:
                            lines_norestore_USE += [
                                """<tr style="border:1px;color:black;"><td align="center" rowspan="{}">可用性</td><td align="center">{}</td><td align="center">{}  {} 次</td><td align="center">{}</td><td align="center">{}</td><td align="center">{}</td></tr>""".format(
                                    nostore_num, i, j, alertlist[i][j]['sum'], hostlist, alertlist[i][j]['lastime'], alertlist[i][j]['status'])]
                            category_count_USE_no += 1
                        else:
                            lines_norestore_USE += [
                                """<tr style="border:1px;color:black;"><td align="center">{}</td><td align="center">{}  {} 次</td><td align="center">{}</td><td align="center">{}</td><td align="center">{}</td></tr>""".format(
                                    i, j, alertlist[i][j]['sum'], hostlist, alertlist[i][j]['lastime'],
                                    alertlist[i][j]['status'])]
                    elif alertlist[i][j]['category'] == 'EXP':
                        nostore_num = _count(alertlist, 'EXP', '未恢复')
                        if category_count_EXP_no == 0:
                            lines_norestore_EXP += [
                                """<tr style="border:1px;color:black;"><td align="center" rowspan="{}">体验</td><td align="center">{}</td><td align="center">{}  {} 次</td><td align="center">{}</td><td align="center">{}</td><td align="center">{}</td></tr>""".format(
                                    nostore_num, i, j, alertlist[i][j]['sum'], hostlist, alertlist[i][j]['lastime'], alertlist[i][j]['status'])]
                            category_count_EXP_no += 1
                        else:
                            lines_norestore_EXP += [
                                """<tr style="border:1px;color:black;"><td align="center">{}</td><td align="center">{}  {} 次</td><td align="center">{}</td><td align="center">{}</td><td align="center">{}</td></tr>""".format(
                                    i, j, alertlist[i][j]['sum'], hostlist, alertlist[i][j]['lastime'],
                                    alertlist[i][j]['status'])]
                    elif alertlist[i][j]['category'] == 'OTH':
                        nostore_num = _count(alertlist, 'OTH', '未恢复')
                        if category_count_OTH_no == 0:
                            lines_norestore_OTH += [
                                """<tr style="border:1px;color:black;"><td align="center" rowspan="{}">其他</td><td align="center">{}</td><td align="center">{}  {} 次</td><td align="center">{}</td><td align="center">{}</td><td align="center">{}</td></tr>""".format(
                                    nostore_num, i, j, alertlist[i][j]['sum'], hostlist, alertlist[i][j]['lastime'], alertlist[i][j]['status'])]
                            category_count_OTH_no += 1
                        else:
                            lines_norestore_OTH += [
                                """<tr style="border:1px;color:black;"><td align="center">{}</td><td align="center">{}  {} 次</td><td align="center">{}</td><td align="center">{}</td><td align="center">{}</td></tr>""".format(
                                    i, j, alertlist[i][j]['sum'], hostlist, alertlist[i][j]['lastime'],
                                    alertlist[i][j]['status'])]
                else:
                    if alertlist[i][j]['category'] == 'USE':
                        restore_num = _count(alertlist, 'USE', '已恢复')
                        # hostlist = init_hosts(alertlist[i][j]['hostname'])
                        if category_count_USE_yes == 0:
                            lines_restore_USE += [
                                """<tr style="border:1px;color:black;"><td align="center" rowspan="{}">可用性</td><td align="center">{}</td><td align="center">{}  {} 次</td><td align="center">{}</td><td align="center">{}</td><td align="center">{}</td></tr>""".format(
                                    restore_num, i, j, alertlist[i][j]['sum'], hostlist, alertlist[i][j]['lastime'], alertlist[i][j]['status'])]
                            category_count_USE_yes += 1
                        else:
                            lines_restore_USE += [
                                """<tr style="border:1px;color:black;"><td align="center">{}</td><td align="center">{}  {} 次</td><td align="center">{}</td><td align="center">{}</td><td align="center">{}</td></tr>""".format(
                                    i, j, alertlist[i][j]['sum'], hostlist, alertlist[i][j]['lastime'],
                                    alertlist[i][j]['status'])]
                    elif alertlist[i][j]['category'] == 'EXP':
                        restore_num = _count(alertlist, 'EXP', '已恢复')
                        if category_count_EXP_yes == 0:
                            lines_restore_EXP += [
                                """<tr style="border:1px;color:black;"><td align="center" rowspan="{}">体验</td><td align="center">{}</td><td align="center">{}  {} 次</td><td align="center">{}</td><td align="center">{}</td><td align="center">{}</td></tr>""".format(
                                    restore_num, i, j, alertlist[i][j]['sum'], hostlist, alertlist[i][j]['lastime'], alertlist[i][j]['status'])]
                            category_count_EXP_yes += 1
                        else:
                            lines_restore_EXP += [
                                """<tr style="border:1px;color:black;"><td align="center">{}</td><td align="center">{}  {} 次</td><td align="center">{}</td><td align="center">{}</td><td align="center">{}</td></tr>""".format(
                                    i, j, alertlist[i][j]['sum'], hostlist, alertlist[i][j]['lastime'],
                                    alertlist[i][j]['status'])]
                    elif alertlist[i][j]['category'] == 'OTH':
                        restore_num = _count(alertlist, 'OTH', '已恢复')
                        if category_count_OTH_yes == 0:
                            lines_restore_OTH += [
                                """<tr style="border:1px;color:black;"><td align="center" rowspan="{}">其他</td><td align="center">{}</td><td align="center">{}  {} 次</td><td align="center">{}</td><td align="center">{}</td><td align="center">{}</td></tr>""".format(
                                    restore_num, i, j, alertlist[i][j]['sum'], hostlist, alertlist[i][j]['lastime'], alertlist[i][j]['status'])]
                            category_count_OTH_yes += 1
                        else:
                            lines_restore_OTH += [
                                """<tr style="border:1px;color:black;"><td align="center">{}</td><td align="center">{}  {} 次</td><td align="center">{}</td><td align="center">{}</td><td align="center">{}</td></tr>""".format(
                                    i, j, alertlist[i][j]['sum'], hostlist, alertlist[i][j]['lastime'],
                                    alertlist[i][j]['status'])]
    # print(lines_norestore)
    # print(lines_restore)
    # print(html)
    html_all = html + '\n' + ''.join(lines_norestore_USE) + '\n' + ''.join(lines_norestore_EXP) + '\n' + ''.join(
        lines_norestore_OTH) + '\n' + html2 + '\n' + ''.join(lines_restore_USE) + '\n' + ''.join(
        lines_restore_EXP) + '\n' + ''.join(lines_restore_OTH) + '\n' + html3
    return html_all



if __name__ == '__main__':
    r = redis.StrictRedis(host='127.0.0.1', port=6379)
    subjectlist=r.keys()
    problemlist = {}
    resovelist = {}
    for i in subjectlist:
        try:
            # print(i.split('_'))
            if i.split('_')[1] == '1 ':
                # print(r.get(i))
                problemlist[i.split('_')[0]] = r.get(i)
            elif i.split('_')[1] == '0 ':
                # print(r.get(i))
                resovelist[i.split('_')[0]] = r.get(i)
        except Exception as e:
            pass

    # 根据结果集生成 html
    alarmresult = {}
    problem = alert()
    alarmresult = problem.sort(problemlist, resovelist)
    # print(alarmresult)
    html_result = problem.compress(alarmresult)
    # print(html_result)
    result_html = init_html(html_result)
    # send mail
    send_mail(result_html)
    # init redis
    for i in subjectlist:
        r.delete()




