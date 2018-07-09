#!/use/bin/env python
# -*- coding:utf-8 -*-
# new agent 

"""
定时收集 redis 告警，入库，并清空 redis
"""
import redis
import MySQLdb

def alert_db(problemlist, resovelist):
    """
    入库
    """
    db = MySQLdb.connect(host="127.0.0.1", user='root',
                         port=3306, passwd="123456", db="radar")
    cursor = db.cursor()
    # 录入未恢复告警 status = 0
    for i in problemlist.keys():
        alert_id = i.split('_')[0]
        trigger_name = str(problemlist[i])[2:-1].split('#')[0]
        host = str(problemlist[i])[:-1].split('#')[1]
        datetime = str(problemlist[i])[:-1].split('#')[4] + \
            ' ' + str(problemlist[i])[:-1].split('#')[3]
        message = str(problemlist[i])[:-1].split('#')[2]
        # cursor.execute("SELECT id, level_id FROM skynet_levels")
        # data = cursor.fetchall()
        sql = """INSERT INTO skynet_alerts(
            alert_id, trigger_name, host, datetime, update_time, message, status) VALUES ('%s', '%s', '%s', '%s', NOW(), '%s', 1)""" \
            % (alert_id, trigger_name, host, datetime, message)
        try:
            cursor.execute(sql)
            db.commit()
        except:
            db.rollback()
    
    # 更新已恢复告警
    for j in resovelist.keys():
        resove_alert = j.split('_')[0]
        cursor.execute(
            "SELECT STATUS FROM skynet_alerts WHERE ALERT_ID = '{}'".format(resove_alert))
        data = cursor.fetchall()
        for result in data:
            resove_status = result[0]
            if resove_status == '':
                pass
            elif resove_status == '1':
                sql = "UPDATE skynet_alerts SET STATUS = 0 WHERE ALERT_ID = '{}'".format(
                    resove_alert)
                try:
                    cursor.execute(sql)
                    db.commit()
                except:
                    db.rollback()
    db.close()


if __name__ == '__main__':
    r = redis.StrictRedis(host='127.0.0.1', port=6379)
    subjectlist = r.keys()
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
    # print(problemlist)
    alert_db(problemlist, resovelist)
    # 清空 redis
    # for i in subjectlist:
    #     r.delete(i)
