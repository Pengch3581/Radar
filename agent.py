#!/use/bin/env python
# -*- coding:utf-8 -*-

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
    
    print(len(resovelist.keys()))




