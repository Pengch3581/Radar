import MySQLdb
import re
import greenstalk
import json


class task(object):

    def __init__(self):
        self.queue = greenstalk.Client(host='127.0.0.1', port=11300)

    def put(self, name, job):
        self.queue.use(name)
        self.queue.put(job, delay=5)

    def get(self, name):
        self.queue.watch(name)
        job = self.queue.reserve()
        self.queue.delete(job)
        return job.body

    def close(self):
        self.queue.close()


def daily_report():
    # 发送日报


def weekly_report():
    pass

def monthly_report():
    pass

# 收敛模块，定时处理告警表，存入收敛信息表中
def group_alert():
    ALERT_WEB = 'webcheck +is +warning'
    db = MySQLdb.connect(host="127.0.0.1", user='root',
                         port=3306, passwd="123456", db="radar")
    cursor = db.cursor()

    # 更新收敛表
    cursor.execute(
        "select alert_id from skynet_group_alerts where status = '1'")
    data_group_alert = cursor.fetchall()
    # group_alertdata is tuple 元组
    # print(type(group_alertdata))
    for id in data_group_alert:
        result = id[0]
        if result == '':
                pass
        else:
            cursor.execute("SELECT status FROM skynet_alerts WHERE ALERT_ID = '{}'".format(result))
            alert_status = cursor.fetchall()
            if len(alert_status) != 1:
                print("error!")
                continue
            sql = "UPDATE skynet_group_alerts SET STATUS = {} WHERE ALERT_ID = '{}'".format(
                alert_status[0][0], result)
            try:
                cursor.execute(sql)
                db.commit()
            except:
                db.rollback()

    # 读取告警表中目前未恢复的告警
    cursor.execute(
        "select alert_id,trigger_name,host,datetime,update_time,message from skynet_alerts where status != '0'")
    data_alert = cursor.fetchall()
    for i in data_alert:
        GROUP_ALERT_EXIT = 0
        alert_problem = i[1]
        webcheck_alert = re.compile(ALERT_WEB)
        # web_testfail = re.compile(ALERT_WEB[0])
        if webcheck_alert.search(alert_problem):
            alert_level = 'P1'
            alert_host = i[2]
            try:
                alert_server = i[1].split(' ')[0]
            except:
                pass
            alert_id = i[0]
            problem_id = 1
            create_time = i[3]
            # update_time = NOW()
            status = 1
            # 查询告警是否已经存在，选择 INSERT or UPDATE
            cursor.execute(
                "select host,alert_server,alert_count from skynet_group_alerts where status != '0'")
            date_group_alert = cursor.fetchall()
            for j in date_group_alert:
                # 更新
                alert_count = 1
                if alert_host == j[0] and alert_server == j[1]:
                    GROUP_ALERT_EXIT = 1
                    alert_count = int(j[2]) + 1
                    sql = """UPDATE skynet_group_alerts SET update_time=NOW(), alert_count='{}', alert_id='{}' where host='{}' and alert_server='{}'""".format(alert_count, alert_id, alert_host, alert_server)
                    try:
                        cursor.execute(sql)
                        db.commit()
                    except Exception as e:
                        print(e)
                        db.rollback()
            # 插入
            if GROUP_ALERT_EXIT == 0:
                sql = """INSERT INTO skynet_group_alerts(
                    alert_level, host, alert_server, alert_name, alert_id, problem_id, create_time, update_time, alert_count, status) VALUES 
                    ('{}', '{}', '{}', '{}', '{}', '{}', '{}', NOW(), '1', '{}')""".format(alert_level, alert_host, alert_server, alert_problem, alert_id, problem_id, create_time, status)
                try:
                    cursor.execute(sql)
                    db.commit()
                except:
                    db.rollback()
    db.close()
    

# 匹配模块，定时匹配收敛模块，匹配成功则添加任务
def rule_match():
    db = MySQLdb.connect(host="127.0.0.1", user='root',
                         port=3306, passwd="123456", db="radar")
    cursor = db.cursor()
    cursor.execute(
        "select host,alert_server from skynet_group_alerts where status = '1'")
    date = cursor.fetchall()
    # 推入心跳包消息队列
    async_task = task()
    heartbody = json.dumps({
        'host': 'heartbeat',
        'server': 'heartbeat',
    })
    async_task.put('ast_webcheck_task', heartbody)
    for i in date:
        alert_server = i[1].split('S')[0] + i[1].split('S')[1]
        alert_ip = i[0].split('/')[1]
        # 推入消息队列
        async_task = task()
        body = json.dumps({
            'host': alert_ip,
            'server': alert_server,
        })
        async_task.put('ast_webcheck_task', body)
        # print(async_task.get(name='ast_webcheck_task'))
        async_task.close()
        # print(alert_server, alert_ip)
        sql = """UPDATE skynet_group_alerts SET update_time=NOW(), status='2' where host='{}' and alert_server='{}'""".format(
            i[0], i[1])
        try:
            cursor.execute(sql)
            db.commit()
        except:
            db.rollback()
    db.close()
    

# 执行模块，可以使用 api 的方式


if __name__ == '__main__':
    group_alert()
    rule_match()
