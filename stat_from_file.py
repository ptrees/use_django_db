import re,sys
from stats import MatchStat
from time import sleep
import threading

try:
    f=open(sys.argv[1])
except:
    f=open('error.log')

match_list=[]
for l in f.readlines():
    r=re.findall("matchid:(\d+)",l)[0]
    if r!='':
        match_list.append(int(r.strip()))

ms=MatchStat()
threads=[]
for i in match_list:
    t=threading.Thread(target=ms.stat_match,args=(i,))
    threads.append(t)
    t.start()
    sleep(1)

for t in threads:
    t.join()

sys.exit()