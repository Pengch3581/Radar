#!/use/bin/env python
# -*- coding:utf-8 -*-

import redis
import os, sys, re
import smtplib
import datetime

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

ALERT_LEVEL = {'P0':['Disk +dmesg +error +on', 'MySQL +is +down +on', 'is +Down', 'Disk +Read-only +on'],
               'P1': ['has +deadlock +on', 'MySQL +has +just +been +restarted', 'has +just +been +restarted', 'Free +disk +space +is +less +than +10%', 'tcp_80 +is +down +on', 'FATAL +Error +on'],
               'P2': ['JAVA.rsp_time +is +over', 'BLOCKED +is +over +20 +on', 'webcheck +is +warning +on', 'JAVA.CPU.Usage +is +over', 'gameport +is +warning +on', 'web.test.fail +is +warning +on', 'Free +disk +space +is +less +than +15%', 'JAVA.OldGC +is +over +92%', 'Network +incoming +traffic +is +over', 'MySQL +CPU +Usage +is +over +600%', 'Time: +Offset +over +30 +second']}

ALERT_LEVEL_USE = {'Disk +dmesg +error':'P0', 'MySQL +is +down':'P0', 'is +DOWN':'P0', 'Disk +Read-only':'P0',
                'has +deadlock':'P1', 'MySQL +has +just +been +restarted':'P1', 'has +just +been +restarted':'P1',
                'BLOCKED +is +over +20 +on':'P2', 'webcheck +is +warning':'P2',  'gameport +is +warning':'P2',
                'web.test.fail +is +warning +on':'P2', 'MySQL +QPS +is +over': 'P2',
                'JAVA.OldGC +is +over +%92': 'P2', 'serviceport +is +warning': 'P2'}

ALERT_LEVEL_EXP = {'JAVA.rsp_time +is +over':'P2', 'JAVA.CPU.Usage +is +over':'P2', 'MySQL +CPU +Usage +is +over': 'P2', 'Processor +load +is +high': 'P2',
                   'Ping +response +time +is +over +200ms': 'P2', 'Offset +over +30 +second': 'P2', 'Free +disk +space +is +less +than +10%': 'P2',
                   'Free +disk +space +is +less +than +15%': 'P3', 'Disk +I/O +is +overloaded': 'P2',  'Network +incoming +traffic +is +over +200M': 'P2',
                   'Network +outcoming +traffic +is +over +200M': 'P2'}

base_html = """
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="http://www.w3.org/1999/xhtml">

<head>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta http-equiv="Content-Type" content="text/html; charset=UTF-8">
    <title>告警日报</title>
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
                                            <p style="font-family: sans-serif; font-size: 14px; font-weight: normal; margin: 0; Margin-bottom: 0px; font-size: 200%; color: #ffffff">告警日报</p>
                                        </td>
                                    </tr>
                                </table>
"""
date_html = """
                                <table cellspacing="1" cellpadding="1" border="0">
                                    <tr>
                                        <td style="font-family: sans-serif; font-size: 14px; vertical-align: top;">
                                            <p style="font-family: sans-serif; font-size: 14px; font-weight: normal; margin: 0; Margin-bottom: 40px; font-size: 90%; color: white; padding-bottom:1px;">{0}</p>
                                        </td>
                                    </tr>
                                </table>
                                <!-- <table border="0" cellpadding="0" cellspacing="0" style="border-collapse: separate; mso-table-lspace: 0pt; mso-table-rspace: 0pt; width: 100%;">
                    <tr>
                      <td style="font-family: sans-serif; font-size: 14px; vertical-align: top;">
                        <p style="font-family: sans-serif; font-size: 14px; font-weight: normal; margin: 0; Margin-bottom: 15px; font-size: 120%; color: #9A9998"><u>今日告警</u></p>
                        <div style="width: 100%; height: 110px;">
                          <div style="width: 10%; float: left; height: 100px; margin-right: 5px; color: white;">
                            <span style="height: 50px; line-height: 50px; width: 100%; display: block; font-weight: bold;">未恢复报警</span>
                            <span style="height: 30px; line-height: 30px; width: 100%; display: block; background-color: #2FF5FE; font-size: 120%">12次</span>
                          </div>
                          <div style="width: 10%; float: left; height: 100px; margin-right: 5px; color: white;">
                            <span style="height: 50px; line-height: 50px; width: 100%; display: block; font-weight: bold;">高级别告警</span>
                            <span style="height: 30px; line-height: 30px; width: 100%; display: block; background-color: #2FF5FE; font-size: 120%">1次</span>
                          </div>
                        </div>
                      </td>
                    </tr>
                  </table> -->
"""

dailycount_html = """
                                <!-- 今日告警统计模块 -->
                                <table cellspacing="3" cellpadding="3" border="0">
                                    <tr>
                                        <td style="font-family: sans-serif; font-size: 14px; vertical-align: top;">
                                            <p style="font-family: sans-serif; font-size: 14px; font-weight: normal; margin: 0; Margin-bottom: 5px; font-size: 120%; color: #9A9998; padding-bottom:1px; border-bottom:2px solid #3199A4">今日告警统计</p>
                                        </td>
                                    </tr>
                                </table>
                                <table cellspacing="3" cellpadding="3" border="0">
                                    <tr>
                                        <td style="width: 110px; font-weight: bold; font-size: 90%; color: white">未恢复告警</td>
                                        <td style="width: 110px; font-weight: bold; font-size: 90%; color: white">高级别告警</td>
                                        <td style="width: 110px; font-weight: bold; font-size: 90%; color: white">总告警</td>
                                        <td style="width: 110px; font-weight: bold; font-size: 90%; color: white">数据备份失败</td>
                                        <td style="width: 110px; font-weight: bold; font-size: 90%; color: white">日志备份失败</td>
                                    </tr>
                                </table>
                                <table cellspacing="4" cellpadding="3" border="0">
                                    <tr>
                                        <td style="width: 110px; background-color: #32C3D1; font-size: 100%; font-weight: bold; color: white">{0}次</td>
                                        <td style="width: 110px; background-color: #32C3D1; font-size: 100%; font-weight: bold; color: white">{1}次</td>
                                        <td style="width: 110px; background-color: #32C3D1; font-size: 100%; font-weight: bold; color: white">{2}次</td>
                                        <td style="width: 110px; background-color: #32C3D1; font-size: 100%; font-weight: bold; color: white">N/A次</td>
                                        <td style="width: 110px; background-color: #32C3D1; font-size: 100%; font-weight: bold; color: white">N/A次</td>
                                    </tr>
                                </table>
                                <table cellspacing="3" cellpadding="3" border="0">
                                    <tr>
                                        <td style="width: 110px; font-weight: bold; font-size: 90%; color: white">服务树异常服</td>
                                        <td style="width: 110px; font-weight: bold; font-size: 90%; color: white">服务树新增</td>
                                        <td style="width: 110px; font-weight: bold; font-size: 90%; color: white">新服清档失败</td>
                                        <td style="width: 110px; font-weight: bold; font-size: 90%; color: white">审计异常次数</td>
                                    </tr>
                                </table>
                                <table cellspacing="4" cellpadding="3" border="0">
                                    <tr>
                                        <td style="width: 110px; background-color: #32C3D1; font-size: 100%; font-weight: bold; color: white">N/A次</td>
                                        <td style="width: 110px; background-color: #32C3D1; font-size: 100%; font-weight: bold; color: white">N/A次</td>
                                        <td style="width: 110px; background-color: #32C3D1; font-size: 100%; font-weight: bold; color: white">N/A次</td>
                                        <td style="width: 110px; background-color: #32C3D1; font-size: 100%; font-weight: bold; color: white">N/A次</td>
                                    </tr>
                                </table>
"""

importalert_title_html = """
                                <!-- 重要告警模块 -->
                                <table cellspacing="3" cellpadding="3" border="0">
                                    <tr>
                                        <td style="font-family: sans-serif; font-size: 14px; vertical-align: top;">
                                            <p style="font-family: sans-serif; font-size: 14px; font-weight: normal; margin: 0; Margin-bottom: 15px; margin-top: 15px; font-size: 120%; color: #9A9998; padding-bottom:1px; border-bottom:2px solid #3199A4">重要告警</p>
                                        </td>
                                    </tr>
                                </table>
"""

importalert_content_html = """
                                <table cellspacing="0" cellpadding="7" border="0">
                                    <tr>
                                        <td style="width: 300px; font-weight: bold; font-size: 80%; color: #9A9998; border: 1px solid #24737B;">告警：{0}</td>
                                        <td style="width: 300px; font-weight: bold; font-size: 80%; color: #9A9998; border: 1px solid #24737B;">影响范围：{1}</td>
                                    </tr>
                                    <tr>
                                        <td style="width: 300px; font-weight: bold; font-size: 80%; color: #9A9998; border: 1px solid #24737B;">类型：N/A</td>
                                        <td style="width: 300px; font-weight: bold; font-size: 80%; color: #9A9998; border: 1px solid #24737B;">级别：{2}</td>
                                    </tr>
                                    <tr>
                                        <td style="width: 300px; font-weight: bold; font-size: 80%; color: #9A9998; border: 1px solid #24737B;">状态：{3}</td>
                                        <td style="width: 300px; font-weight: bold; font-size: 80%; color: #9A9998; border: 1px solid #24737B;">时间：{4} {5}</td>
                                    </tr>
                                    <tr>
                                        <td colspan="2" style="width: 500px; font-weight: bold; font-size: 80%; color: #9A9998; border:1px solid #24737B;">描述：{6}</td>
                                    </tr>
                                </table>
                                <table cellspacing="0" cellpadding="0" border="0">
                                    <tr>
                                        <td>
                                            <hr width="600" color="#68686A" />
                                        </td>
                                    </tr>
                                </table>
"""

importalert_line_html = """
                                <table cellspacing="0" cellpadding="7" border="0">
                                    <tr>
                                        <td style="width: 300px; font-weight: bold; font-size: 80%; color: #9A9998; border: 1px solid #24737B;">告警：</td>
                                        <td style="width: 300px; font-weight: bold; font-size: 80%; color: #9A9998; border: 1px solid #24737B;">影响范围：</td>
                                    </tr>
                                    <tr>
                                        <td style="width: 300px; font-weight: bold; font-size: 80%; color: #9A9998; border: 1px solid #24737B;">类型：</td>
                                        <td style="width: 300px; font-weight: bold; font-size: 80%; color: #9A9998; border: 1px solid #24737B;">级别：</td>
                                    </tr>
                                    <tr>
                                        <td style="width: 300px; font-weight: bold; font-size: 80%; color: #9A9998; border: 1px solid #24737B;">状态：</td>
                                        <td style="width: 300px; font-weight: bold; font-size: 80%; color: #9A9998; border: 1px solid #24737B;">时间：</td>
                                    </tr>
                                    <tr>
                                        <td colspan="2" style="width: 500px; font-weight: bold; font-size: 80%; color: #9A9998; border:1px solid #24737B;">描述：</td>
                                    </tr>
                                </table>
                                <table cellspacing="0" cellpadding="0" border="0">
                                    <tr>
                                        <td>
                                            <hr width="600" color="#68686A" />
                                        </td>
                                    </tr>
                                </table>
"""

nonalert_title_html = """
                                <!-- 未恢复告警模块 -->
                                <table cellspacing="3" cellpadding="3" border="0">
                                    <tr>
                                        <td style="font-family: sans-serif; font-size: 14px; vertical-align: top;">
                                            <p style="font-family: sans-serif; font-size: 14px; font-weight: normal; margin: 0; Margin-bottom: 15px; margin-top: 15px; font-size: 120%; color: #9A9998; padding-bottom:1px; border-bottom:2px solid #3199A4">未恢复告警</p>
                                        </td>
                                    </tr>
                                </table>
                                <table cellspacing="0" cellpadding="7" border="0">
                                    <tr>
                                        <th style="width: 30px; font-weight: bold; font-size: 80%; color: #9A9998; border: 1px solid #24737B;">级别</th>
                                        <th style="width: 50px; font-weight: bold; font-size: 80%; color: #9A9998; border: 1px solid #24737B;">类型</th>
                                        <th style="width: 500px; font-weight: bold; font-size: 80%; color: #9A9998; border: 1px solid #24737B;">告警</th>
                                        <th style="width: 300px; font-weight: bold; font-size: 80%; color: #9A9998; border: 1px solid #24737B;">主机</th>
                                        <th style="width: 100px; font-weight: bold; font-size: 80%; color: #9A9998; border: 1px solid #24737B;">时间</th>
                                        <th style="width: 60px; font-weight: bold; font-size: 80%; color: #9A9998; border: 1px solid #24737B;">状态</th>
                                    </tr>
"""

nonalert_content_html = """
                                    <tr>
                                        <td style="width: 30px; font-weight: bold; font-size: 80%; color: #9A9998; border: 1px solid #24737B;">{0}</td>
                                        <td style="width: 50px; font-weight: bold; font-size: 80%; color: #9A9998; border: 1px solid #24737B;">N/A</td>
                                        <td style="width: 500px; font-weight: bold; font-size: 80%; color: #9A9998; border: 1px solid #24737B;">{1}</td>
                                        <td style="width: 300px; font-weight: bold; font-size: 80%; color: #9A9998; border: 1px solid #24737B;">{2}</td>
                                        <td style="width: 100px; font-weight: bold; font-size: 80%; color: #9A9998; border: 1px solid #24737B;">{3}</td>
                                        <td style="width: 60px; font-weight: bold; font-size: 80%; color: #9A9998; border: 1px solid #24737B;">{4}</td>
                                    </tr>
"""

nonalert_line_html = """
                                    <tr>
                                        <td style="width: 30px; font-weight: bold; font-size: 80%; color: #9A9998; border: 1px solid #24737B;"></td>
                                        <td style="width: 50px; font-weight: bold; font-size: 80%; color: #9A9998; border: 1px solid #24737B;"></td>
                                        <td style="width: 500px; font-weight: bold; font-size: 80%; color: #9A9998; border: 1px solid #24737B;"></td>
                                        <td style="width: 300px; font-weight: bold; font-size: 80%; color: #9A9998; border: 1px solid #24737B;"></td>
                                        <td style="width: 100px; font-weight: bold; font-size: 80%; color: #9A9998; border: 1px solid #24737B;"></td>
                                        <td style="width: 60px; font-weight: bold; font-size: 80%; color: #9A9998; border: 1px solid #24737B;"></td>
                                    </tr>
"""

nonalert_end_html = """
                                </table>
"""

new_server_title = """
                  <!-- 新服模块 -->
                  <table cellspacing="3" cellpadding="3" border="0">
                    <tr>
                      <td style="font-family: sans-serif; font-size: 14px; vertical-align: top;">
                        <p style="font-family: sans-serif; font-size: 14px; font-weight: normal; margin: 0; Margin-bottom: 15px; margin-top: 15px; font-size: 120%; color: #9A9998; padding-bottom:1px; border-bottom:2px solid #3199A4">新服情况</p>
                      </td>
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

def create_recomplie(alert_num):
    re_argv = '('
    for i in alert_num:
        i += '|'
        re_argv += i
    re_argv = re_argv[:-1]
    re_argv += ')'
    return re_argv

class html_alert():
    '''
    构建告警 html 邮件模版
    '''
    def __init__(self):
        try:
            today = datetime.datetime.now().strftime("%Y-%m-%d")
            self.html_test = str(date_html).format(today)
        except FileNotFoundError as identifier:
            pass

    def daily_count(self, problemlist, resovelist):
        '''
        汇总每日告警信息
        '''
        # 告警总数
        alert_count = len(problemlist.keys())
        # 未恢复告警数
        no_resover = 0
        for i in problemlist.keys():
            if i not in resovelist.keys():
                no_resover += 1
        # 高级别告警数
        high_alert = 0
        a = re.compile(create_recomplie(ALERT_LEVEL['P0']))
        for i in problemlist.keys():
            if a.search(str(problemlist[i])[1:]):
                high_alert += 1
        return dailycount_html.format(no_resover, high_alert, alert_count)

    def import_alert(self, problemlist, resovelist):
        """
        每日重要告警，统计非工作时间内 P0 P1 级别告警
        """
        import_alert_html = importalert_title_html
        alert_level_P0 = re.compile(create_recomplie(ALERT_LEVEL['P0']))
        alert_level_P1 = re.compile(create_recomplie(ALERT_LEVEL['P1']))
        import_count = 0
        for i in problemlist.keys():
            if alert_level_P0.search(str(problemlist[i])[1:]):
                # print(str(problemlist[i])[2:-1].split('#'))
                # for j in ALERT_LEVEL['P0']:
                    # a = re.compile(j)
                    # if a.search(str(problemlist[i])):
                        # alert_name = j
                alert_name = str(problemlist[i])[:-1].split('#')[2]
                alert_range = str(problemlist[i])[:-1].split('#')[1]
                alert_date = str(problemlist[i])[:-1].split('#')[4]
                alert_time = str(problemlist[i])[:-1].split('#')[3]
                alert_description = str(problemlist[i])[:-1].split('#')[0]
                alert_level = 'P0'
                if i in resovelist.keys():
                    alert_status = "已恢复"
                else:
                    alert_status = "未恢复"
                alert_time_compile = re.compile('(0[0123456789]|1[89]|2[0123])\:\d\d\:\d\d')
                if alert_time_compile.search(alert_time):
                    import_alert_html += '\n' 
                    import_alert_html += importalert_content_html.format(
                        alert_name, alert_range, alert_level, alert_status, alert_date, alert_time, alert_description)
                    import_count += 1
            elif alert_level_P1.search(str(problemlist[i])[1:]):
                # for j in ALERT_LEVEL['P0']:
                #     a = re.compile(j)
                #     if a.search(str(problemlist[i])):
                #         alert_name = j
                alert_name = str(problemlist[i])[:-1].split('#')[2]
                alert_range = str(problemlist[i])[:-1].split('#')[1]
                alert_date = str(problemlist[i])[:-1].split('#')[4]
                alert_time = str(problemlist[i])[:-1].split('#')[3]
                alert_description = str(problemlist[i])[:-1].split('#')[0]
                alert_level = 'P1'
                if i in resovelist.keys():
                    alert_status = "已恢复"
                else:
                    alert_status = "未恢复"
                alert_time_compile = re.compile(
                    '(0[0123456789]|1[89]|2[0123])\:\d\d\:\d\d')
                if alert_time_compile.search(alert_time):
                    import_alert_html += '\n' 
                    import_alert_html += importalert_content_html.format(
                        alert_name, alert_range, alert_level, alert_status, alert_date, alert_time, alert_description)
                    import_count += 1
        if import_count == 0:
            import_alert_html += '\n' 
            import_alert_html += importalert_line_html
        return import_alert_html
        

    def non_alert(self, problemlist, resovelist):
        """
        未恢复告警模块
        """
        non_alert_html = nonalert_title_html + '\n'
        non_alert_level_P0 = re.compile(create_recomplie(ALERT_LEVEL['P0']))
        non_alert_level_P1 = re.compile(create_recomplie(ALERT_LEVEL['P1']))
        non_alert_level_P2 = re.compile(create_recomplie(ALERT_LEVEL['P2']))
        non_alert_count = 0
        for i in problemlist.keys():
            if i not in resovelist.keys():
                non_alert_status = "未恢复"
                non_alert_range = str(problemlist[i])[:-1].split('#')[1]
                non_alert_time = str(problemlist[i])[:-1].split('#')[3]
                non_alert_name = str(problemlist[i])[:-1].split('#')[2]
                non_alert_count += 1
                if re.compile(non_alert_level_P0).search(str(problemlist[i])):
                    non_alert_level = 'P0'
                elif re.compile(non_alert_level_P1).search(str(problemlist[i])):
                    non_alert_level = 'P1'
                elif re.compile(non_alert_level_P2).search(str(problemlist[i])):
                    non_alert_level = 'P2'
                else:
                    non_alert_level = 'Other'
                non_alert_html += nonalert_content_html.format(non_alert_level, non_alert_name, non_alert_range, non_alert_time, non_alert_status)
        if non_alert_count == 0:
            non_alert_html += nonalert_line_html
        non_alert_html += nonalert_end_html
        return non_alert_html

                
    
    def new_server(self, parameter_list):
        pass


def send_mail(html):
    sender = "report@contoso.com"
    receivers = ['pengchao@game-reign.com']
    msg = MIMEMultipart()
    msg['Subject'] = '[告警日报] {}'.format(datetime.date.today())
    msg['From'] = sender
    msg['To'] = ', '.join(receivers)
    part = MIMEText(html, 'html')
    msg.attach(part)
    s = smtplib.SMTP('localhost')
    s.sendmail(sender, receivers, msg.as_string())
    s.quit()

if __name__ == '__main__':
    r = redis.StrictRedis(host='127.0.0.1', port=6379)
    subjectlist=r.keys()
    problemlist = {}
    resovelist = {}
    for i in subjectlist:
        try:
            if str(i).split('_')[1][0] == "1":
                problemlist[str(i).split('_')[0][2:]] = r.get(i)
            elif str(i).split('_')[1][0] == "0":
                resovelist[str(i).split('_')[0][2:]] = r.get(i)
        except Exception as e:
            print(e)
    
    html_all = html_alert()
    today = datetime.datetime.now().strftime("%Y-%m-%d")
    html_total = base_html + '\n' + date_html.format(today) + '\n'
    html_total += html_all.daily_count(problemlist, resovelist)
    html_total += '\n' 
    html_total += html_all.import_alert(problemlist, resovelist)
    html_total += '\n'
    html_total += html_all.non_alert(problemlist, resovelist)
    html_total += '\n'
    html_total += new_server_title
    html_total += '\n'
    html_total += end_html
    send_mail(html_total)

    

    
        

