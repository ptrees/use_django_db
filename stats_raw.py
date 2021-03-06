import requests,re
import MySQLdb

class MatchInfo():
    def __init__(self):
        self.con_info="host='localhost',port=3306,user='django_admin',passwd='123456',db='django_web'"

#coding:utf-8
import requests,re
from bs4 import BeautifulSoup
import threading
from django.db import connection
from time import sleep
import logging
logformat=logging.Formatter("%(message)s %(asctime)s %(filename)s[line:%(lineno)d] \
                     %(levelname)s ")
loginfo=logging.getLogger('info')
logerror=logging.getLogger('error')
finfo=logging.FileHandler('info.log')
ferror=logging.FileHandler('error.log')
finfo.setFormatter(logformat)
ferror.setFormatter(logformat)
loginfo.addHandler(finfo)
logerror.addHandler(ferror)

BASE_URL="http://300report.jumpw.com/"
STARTID=67482286
TIME_SLEEP=2
FLAG=0

class MatchStat():
    def stat_match(self,matchid):
        try:
            html=requests.get(BASE_URL+'match.html?id=%d'%matchid)
            if html.status_code==200:
                soup=BeautifulSoup(html.text,'lxml')
                trs=soup.find_all('tr')
                query=[]
                if len(trs)==16:
                #datamsg=soup.findAll(attr={'class':'datamsg'})           #类型:战场 人头数:62/51 比赛时间:2017-03-22 22:19:13 比赛用时:41分40秒
                    datamsg=soup.find_all('span')[1].next_element.next_element.split()
                    info_type=datamsg[0].split(':')[1]
                    if info_type=='战场':        #战场，竞技场数据格式不同，偏移量为4
                        FLAG=-2
                    else:
                        FLAG=2
                    print FLAG
                    info_date=datamsg[2].split(':')[1]
                    info_time=datamsg[3]
                    playtime=datamsg[4].split(":")[1]
                    playtime_h=re.findall("(\d+)小时",playtime)[0] if re.match('小时',playtime) else "00"
                    playtime_m=re.findall("(\d+)分",playtime)[0] if re.match('分',playtime) else "00"
                    playtime_s=re.findall("(\d+)秒",playtime)[0] if re.match('秒',playtime) else "00"
                    info_playtime=str(playtime_h)+':'+str(playtime_m)+':'+str(playtime_s)
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
                        print tds[15+FLAG].img['title']
                        items=tds[17+FLAG].find_all('img')
                        if len(items)!=0:
                            for j in range(1,len(items)+1):
                                self.writeattr(match_info,'player%s_item%s'%(str(i),str(j)),items[j-1]['title'])
                                print items[j-1]['title']
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
                            save()
                            loginfo.info("成功存储比赛信息，matchid:%d"%matchid)
                            #connection.close()
                        except IOError,e:
                            logerror.error("\t\t"+str(e)+"存储详细信息失败,"+"matchid:%d"%matchid)
            else:
                loginfo.warning("match:%d 未获取到比赛信息。"%matchid)


        except IOError,e:
        #except Exception,e:
            logerror.warn(str(e)+"网络连接失败")

    def writeattr(self,classname,key,value):
        try:
            if value:
                setattr(classname,key,value)
        except IndexError:
            logerror.warning("/t/tmatchid:%(matchid)d %(key)s net set!")

    def run(self,num):

        for i in range(int(num)):
            t=threading.Thread(target=self.stat_match,args=(STARTID+i,))
            t.start()
            sleep(TIME_SLEEP)
        self.stat_match(STARTID)




if __name__=='__main__':
    m=MatchStat()
    m.run(sys.argv[1])




