#coding:utf-8
import sys
reload(sys)
sys.setdefaultencoding('utf-8')
sys.dont_write_bytecode = True
# Django specific settings
import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "use_django_db.settings")
import django
django.setup()

import requests,re
from bs4 import BeautifulSoup
from match_stat.models import MatchInfo4 as MatchInfo
import threading
from django.db import connections,close_old_connections
from time import sleep
import logging
logformat=logging.Formatter("%(message)s %(asctime)s %(filename)s[line:%(lineno)d] \
                     %(levelname)s ")
loginfo=logging.getLogger('info')
loginfo.setLevel(logging.INFO)
logerror=logging.getLogger('error')
finfo=logging.FileHandler('info.log')
ferror=logging.FileHandler('error.log')
finfo.setFormatter(logformat)
ferror.setFormatter(logformat)
loginfo.addHandler(finfo)
logerror.addHandler(ferror)

BASE_URL="http://300report.jumpw.com/"
STARTID=67482286
TIME_SLEEP=1
FLAG=0

class MatchStat():
    def stat_match(self,matchid):
        try:
            html=requests.get(BASE_URL+'match.html?id=%d'%matchid)
            if html.status_code==200:
                soup=BeautifulSoup(html.text,'lxml')
                trs=soup.find_all('tr')
                if len(trs)==16:
                #datamsg=soup.findAll(attr={'class':'datamsg'})           #类型:战场 人头数:62/51 比赛时间:2017-03-22 22:19:13 比赛用时:41分40秒
                    datamsg=soup.find_all('span')[1].next_element.next_element.split()
                    match_info=MatchInfo(matchid=matchid)
                    match_info.info_type=datamsg[0].split(':')[1]
                    #print match_info.info_type
                    if match_info.info_type=='战场':        #战场，竞技场数据格式不同，偏移量为4
                        FLAG=-2
                    else:
                        FLAG=2
                    #print FLAG
                    match_info.info_date=datamsg[2].split(':')[1]
                    match_info.info_time=datamsg[3]
                    playtime=datamsg[4].split(":")[1]
                    playtime_h=re.findall("(\d+)小时",playtime)[0] if re.match('小时',playtime) else "00"
                    playtime_m=re.findall("(\d+)分",playtime)[0] if re.match('分',playtime) else "00"
                    playtime_s=re.findall("(\d+)秒",playtime)[0] if re.match('秒',playtime) else "00"
                    match_info.info_playtime=str(playtime_h)+':'+str(playtime_m)+':'+str(playtime_s)
                    trs.pop(8)
                    trs.pop(0)
                    for i in range(1,len(trs)):
                        try:
                            tds=[ t for t in trs[i].children ]
                        except IndexError:
                            continue
                            #print i,matchid
                        self.writeattr(match_info,'player%s_resault'%str(i),True if (trs[i].parent.previous_element.previous_element==u"胜利") else False)
                        if tds[3].a:
                            self.writeattr(match_info,'player%s_name'%str(i),tds[3].a.string.split('(')[0])
                        try:
                            self.writeattr(match_info,'player%s_hero'%str(i),tds[3].a.next_element.next_element.next_element.split('(')[0])
                        except Exception,e:
                            #print i,matchid,e
                            loginfo.warning(e)
                        self.writeattr(match_info,'player%s_user_lv'%str(i),int(re.findall("lv\.(\d+)",str(tds[3]))[0]))
                        self.writeattr(match_info,'player%s_hero_lv'%str(i),int(re.findall("lv\.(\d+)",str(tds[3]))[1]))
                        kills=tds[5].string.split('/')
                        self.writeattr(match_info,'player%s_kills'%str(i),int(kills[0]))
                        self.writeattr(match_info,'player%s_dies'%str(i),int(kills[1]))
                        self.writeattr(match_info,'player%s_helps'%str(i),int(kills[1]))
                        self.writeattr(match_info,'player%s_wins'%str(i),tds[7].string)
                        self.writeattr(match_info,'player%s_soldiers'%str(i),int(tds[11].string))
                        self.writeattr(match_info,'player%s_skill1'%str(i),tds[15+FLAG].img['title'])
                        self.writeattr(match_info,'player%s_skill2'%str(i),tds[15+FLAG].img.next_sibling['title'])
                        #print tds[15+FLAG].img['title']
                        items=tds[17+FLAG].find_all('img')
                        if len(items)!=0:
                            for j in range(1,len(items)+1):
                                self.writeattr(match_info,'player%s_item%s'%(str(i),str(j)),items[j-1]['title'])
                                #print items[j-1]['title']
                        if FLAG==2:
                            self.writeattr(match_info,'player%s_golds'%str(i),tds[13].string)
                            try:
                                gain_golds_exps=tds[21].string.split('/')
                                if len(gain_golds_exps) != 0:
                                    self.writeattr(match_info,'player%s_gain_golds'%str(i),int(gain_golds_exps[0]))
                                    self.writeattr(match_info,'player%s_gain_exp'%str(i),int(gain_golds_exps[1]))
                            except TypeError:
                                continue
                            self.writeattr(match_info,'player%s_jiecao'%str(i),int(tds[23].string))
                            self.writeattr(match_info,'player%s_win_p'%str(i),tds[25].string)
                    try:
                        close_old_connections()
                        match_info.save()
                        loginfo.info("成功存储比赛信息，id:%d"%(matchid-STARTID))
                        print "matchid:%d saved"%matchid
                        #connection.close()
                    except Exception,e:
                        logerror.error("\t\t"+str(e)+"存储数据失败,"+"matchid:%d"%matchid)
            else:
                loginfo.warning("match:%d 未获取到比赛信息。"%matchid)
        except Exception,e:
        #except Exception,e:
            logerror.warn(str(e)+"网络连接失败")

    def writeattr(self,classname,key,value):
        try:
            if value:
                setattr(classname,key,value)
        except IndexError:
            logerror.warning("/t/tmatchid:%(matchid)d %(key)s net set!")

    def run(self,start,end):
        threads=[]
        for i in range(int(start),int(end)):
            #t=threading.Thread(target=self.stat_match,args=(STARTID+i,))
            #threads.append(t)
            #t.start()
            self.stat_match(STARTID+i)
            sleep(TIME_SLEEP)
        #sys.exit()



if __name__=='__main__':
    m=MatchStat()
    try:
        TIME_SLEEP=float(sys.argv[3])
    except:
        pass
    m.run(sys.argv[1],sys.argv[2])


