import netifaces

interfaces = [ i for i in netifaces.interfaces() if i != 'lo' ]
addresses = [ netifaces.ifaddresses(i).get(netifaces.AF_INET) for i in interfaces ]
ip_list = set(i[0]['addr'] for i in addresses if i)
ip_list.add('192.168.42.1')