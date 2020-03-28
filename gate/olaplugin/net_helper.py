import netifaces

interfaces = [ netifaces.ifaddresses(i).get(netifaces.AF_INET) for i in netifaces.interfaces() ]
ip_list = set(i[0]['addr'] for i in interfaces if i)