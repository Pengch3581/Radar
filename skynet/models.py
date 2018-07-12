from django.db import models


# Create your models here.


class Alerts(models.Model):
    """
    告警
    """
    STATUS_CHOICES = (
        ('0', 'restored'),
        ('1', 'no-recovered'),
    ) # 告警状态
    
    alert_id = models.CharField('告警id', max_length=20)
    trigger_name = models.CharField('触发器', max_length=100)
    host = models.CharField('hostname', max_length=50)
    datetime = models.CharField('日期', max_length=100)
    update_time = models.DateField('更新时间')
    message = models.CharField('消息', max_length=100)
    status = models.CharField('告警状态', max_length=1, choices=STATUS_CHOICES)

    def __str__(self):
        return self.alert_id

    class Meta:
        # - 表示逆序
        ordering = ['-datetime']

# 收敛告警表
class Group_alerts(models.Model):
    """
    告警，收敛表
    status
    0 已恢复
    1 未恢复
    2 已处理
    """
    alert_level = models.CharField('告警级别', max_length=10)
    host = models.CharField('告警主机', max_length=100)
    alert_server = models.CharField('告警服务', max_length=100)
    alert_name = models.CharField('告警名称', max_length=200)
    alert_id = models.CharField('最后告警 id', max_length=100)
    problem_id = models.CharField('告警项 id', max_length=100)
    create_time = models.CharField('告警录入时间', max_length=200)
    update_time = models.CharField('告警更新时间', max_length=200)
    alert_count = models.CharField('告警次数', max_length=100)
    status = models.CharField('告警状态', max_length=100)

    def __str__(self):
        return self.alert_name

class Problems(models.Model):
    '''
    告警项
    '''
    problem_name = models.CharField('告警项', max_length=200)
    level = models.CharField('告警登记', max_length=10)

    def __str__(self):
        return self.problem_name

class Levels(models.Model):
    '''
    告警级别
    P0：整机硬件级别不可用
    P1：服务不可用，整机不可用隐患
    P2：体验性告警，服务不可用隐患
    Other：其他
    '''
    level_id = models.CharField('告警级别', max_length=10)

    def __str__(self):
        return self.level_id

      
class Types(models.Model):
    '''
    告警类型
    '''
    type_name = models.CharField('类型名称', max_length=50)

    def __str__(self):
        return self.type_name

