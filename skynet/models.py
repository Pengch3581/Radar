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
    alert_id = models.CharField('告警id', max_length=20 )
    trigger = models.CharField('触发器', max_length=50)
    host = models.CharField('hostname', max_length=30)
    datetime = models.DateField('日期')
    message = models.CharField('消息', max_length=60)
    status = models.CharField('告警状态', max_length=1, choices=STATUS_CHOICES)

    def __str__(self):
        return self.alert_id

    class Meta:
        # - 表示逆序
        ordering = ['-datetime']

class Problems(models.Model):
    '''
    告警项
    '''
    problem_name = models.CharField('告警项', max_length=50)
    level = models.CharField('告警登记', max_length=10)

    def __str__(self):
        return self.problem_name

class Levels(models.Model):
    '''
    告警级别
    '''
    level_id = models.CharField('告警级别', max_length=10)

    def __str__(self):
        return self.level_id

