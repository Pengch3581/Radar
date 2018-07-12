#!/usr/bin/env python
#coding: utf-8
"""
从消息队列获取任务并处理
"""
import greenstalk
import json

__all__ = ['task']

class task(object):

    def __init__(self):
        self.queue = greenstalk.Client(host='127.0.0.1', port=11300)

    def put(self, name, job):
        self.queue.use(name)
        # self.queue.put(job, delay=5)
        self.queue.put(job)

    def get(self, name):
        self.queue.watch(name)
        job = self.queue.reserve()
        self.queue.delete(job)
        return job.body

    def close(self):
        self.queue.close()


def main():
    async_task = task()
    body = json.dumps({
        'host': '106.75.78.106',
        'server': 'zjzr_xianyuandroid_831',
    })
    async_task.put('ast_webcheck_task', body)
    # print(async_task.get(name='ast_webcheck_task'))
    async_task.close()



if __name__ == '__main__':
    main()
