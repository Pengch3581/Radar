import requests
import string
import random
import socket
import struct

RANDOM_IP_POOL=['192.168.10.222/0']
def __get_random_ip():
  str_ip = RANDOM_IP_POOL[random.randint(0,len(RANDOM_IP_POOL) - 1)]
  str_ip_addr = str_ip.split('/')[0]
  str_ip_mask = str_ip.split('/')[1]
  ip_addr = struct.unpack('>I',socket.inet_aton(str_ip_addr))[0]
  mask = 0x0
  for i in range(31, 31 - int(str_ip_mask), -1):
    mask = mask | ( 1 << i)
  ip_addr_min = ip_addr & (mask & 0xffffffff)
  ip_addr_max = ip_addr | (~mask & 0xffffffff)
  return socket.inet_ntoa(struct.pack('>I', random.randint(ip_addr_min, ip_addr_max)))
print(__get_random_ip())



datetime_i = ['2018-06-13','2018-06-12','2018-06-11',"2018-06-10"]
message_i = [
    'Too much work at interrupt, IntrStatus=0x0001',
    'IPVS: incoming ICMP: failed checksum from 61.172.0.X!',
    'NET: N messages suppressed.',
    'UDP: bad checksum. From 221.200.X.X:50279 to 218.62.X.X:1155 ulen 24',
    'kernel: conntrack_ftp: partial 227 2205426703+13'
]
for i in range(1,10000):
    alert_id = i
    s = string.ascii_letters
    trigger = random.choice(s)
    host = __get_random_ip()
    datetime =  random.choice(datetime_i)
    message = random.choice(message_i)
    status = random.choice([0,1])
    data = {'alert_id':alert_id,'trigger':trigger,'host':host,'datetime':datetime,'message':message,'status':status}
    url = 'http://118.190.150.92:8000/token/Alerts/getstocklist/'
    header = {
        'Content-Type': 'application/json',
    }
    html = requests.post(url, json=data, headers=header, auth=('root', 'liubin0252'))
    print(html.text)




