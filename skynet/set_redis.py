#!/usr/local/bin/python
# -*- coding:utf-8 -*-
import redis
import sys
name = sys.argv[1]
subject = sys.argv[2]
message = sys.argv[3]
r = redis.StrictRedis(host='127.0.0.1', port=6379)
r.set(subject, message)