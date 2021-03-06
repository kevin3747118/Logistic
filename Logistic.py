#-*- coding: utf-8 -*-
import time
import urllib.request, urllib.parse
import random
import sys
# import pytesseract
import requests
import os
import string
import datetime
import base64
import queue
import threading
import re


from bs4 import BeautifulSoup
from DB_CONNECTION import connection

# from PIL import Image
# from io import BytesIO

# import numpy as np, matplotlib.pyplot as plt
""" 
貨到時SQLPASS UPDATE STATUS
Load data from sqlpaas
"""

"""
ELK data format
doc = {
    'author': 'kimchy',
    'text': 'Elasticsearch: cool. bonsai cool.',
    'timestamp': datetime.now(),
}
res = es.index(index="test-index", doc_type='tweet', id=1, body=doc)

print(res['created'])

res = es.get(index="test-index", doc_type='tweet', id=1)
print(res['_source'])

es.indices.refresh(index="test-index")
"""
###
"""
doc = {
    'ORD_NUM': '128073154',
    'PACKAGE_NO': '760053488326',
    'PACKAGE_STATUS': {xxx},
    'DELIVERY': {'START_TIME':xxx, 'END_TIME':xxx} 
    'FLAG': '0',
    'UPDATE_TIME': 'xxx'
}
"""


class MyThread(threading.Thread):

    def __init__(self, func):

        super(MyThread, self).__init__()  ### 調用父類的結構函數
        self.func = func  ### 傳入線程函數邏輯
        self._stop_event = threading.Event() ### 線程停止的方法

        self.threadLock = threading.Lock()

    def run(self):

        self.threadLock.acquire()
        self.func()
        self.threadLock.release()

    def stop(self):

        self._stop_event.set()

    #
    # def stopped(self):
    #
    #     return self._stop_event.is_set()

class request(object):

    @classmethod
    def get_page_utf8(cls, url, request_header=None, parameters=None):

        if parameters:
            encode_parameters = urllib.parse.urlencode(parameters).encode('utf-8')
        else:
            encode_parameters = None

        #### 隨機 user-agent 挑選 ####
        foo = [
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2227.1 Safari/537.36',
            'Mozilla/5.0 (compatible, MSIE 11, Windows NT 6.3; Trident/7.0; rv:11.0) like Gecko',
            'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:40.0) Gecko/20100101 Firefox/40.1',
            'Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10_6_7; da-dk) AppleWebKit/533.21.1 (KHTML, like Gecko) Version/5.0.5 Safari/533.21.1',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/42.0.2311.135 Safari/537.36 Edge/12.246',
            'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/52.0.2722.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 6.3; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/53.0.2785.116 Safari/537.36',
            'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/57.0.2987.133 Safari/537.36'
        ]
        user_agent = str(random.choice(foo))
        #### 隨機 user-agent 挑選 ####

        #### 組合 headers ####
        if request_header:
            request_header['User-Agent'] = user_agent
            req = urllib.request.Request(url=url, headers=request_header)
        else:
            req = urllib.request.Request(url=url, headers=({'User-Agent': user_agent}))
        #### 組合 headers ####

        try:
            response = urllib.request.urlopen(req, data=encode_parameters, timeout=180)
            html = BeautifulSoup(response.read().decode('utf-8'), 'lxml')
            response.close()
        except:
            response = urllib.request.urlopen(req, data=encode_parameters, timeout=180)
            html = BeautifulSoup(response.read().decode('big5'), 'lxml')
            response.close()

        return html

    @classmethod
    def random_ip(cls):

        ip = ".".join(str(random.randint(0, 255)) for _ in range(4))

        return ip


###新竹物流### 貨件已由鹿港營業所送達。貨物件數共1件
class hct(request, MyThread):

    SHARE_Q = queue.Queue()
    _WORKER_THREAD_NUM = 2

    @staticmethod
    def b64_encode(string):

        result = base64.b64encode(str(string).encode('utf-8')).decode('utf-8')

        return result

    @classmethod
    def parse_hct(cls, item):

        # pack_no = str(item)
        pack_no = str(item[1])
        ord_num = str(item[0])

        package_no_b64 = hct.b64_encode(pack_no)
        url = 'https://www.hct.com.tw/searchgoods.aspx?no=' + package_no_b64 + "&no2="

        attempts = 0
        while attempts < 3:
            try:
                payload = {
                    'no': package_no_b64,
                    'no2': ''
                }

                headers = {
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                    'Accept-Encoding': 'gzip, deflate, sdch, br',
                    'Accept-Language': 'zh-TW,zh;q=0.8,en-US;q=0.6,en;q=0.4',
                    'Cache-Control': 'max-age=0',
                    'Connection': 'keep-alive',
                    'Host': 'www.hct.com.tw',
                    'referer': "https://www.hct.com.tw/check_code.aspx?v=U2VhcmNoR29vZHMuYXNweD9ubz1PVEkwTlRFeU5UazFOZz09Jm5vMj0=",
                    'Upgrade-Insecure-Requests': '1',
                    'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36',
                    'X-Requested-With': 'XMLHttpRequest'
                    # "X-Forwarded-For": request.random_ip()
                }  # Cookie:ASP.NET_SessionId=tppfd1esuupisj55gddcdlft

                response = requests.request("POST", url, data=payload, headers=headers)
                result = BeautifulSoup(response.text, 'lxml')

                arrival = 0
                hct_list = list()

                # for i in result.find_all('span', {'id': 'lbl_stats'}):
                #     if '查無此配送資料' in i.text:
                #         no_status = 0
                #
                # if no_status == 0:
                #     update(0, pack_no)
                #     break

                if result.find_all('td', {'class': 'pad'}):
                    for i in result.find_all('td', {'class': 'pad'}):
                        text = i.text
                        hct_list.append(text)
                        ### verify package arrival
                        if '送達' in i.text:
                            arrival = 1
                        ### verify package arrival
                        if text is None:
                            connection.mail.send_mail('新竹物流: {}, HTML格式可能改變'.format(pack_no), '物流')
                elif result.find_all('ul', {'class': 'searchHelp'}):
                    connection.mail.send_mail('新竹物流: 可能換方法', str(ord_num))
                else:
                    update(0, pack_no)
                    break

                now = datetime.datetime.today().strftime("%Y-%m%d-%H:%M:%S")

                body = [{'date': hct_list[i],
                         'status': hct_list[i+1],
                         'station': '',
                         'status_code': ''
                        }for i in range(0, len(hct_list), 2)]

                # hct_dict = {hct_list[i]: hct_list[i + 1] for i in range(0, len(hct_list), 2)}

                doc = {
                    'ORD_NUM': ord_num,
                    'PACKAGE_NO': pack_no,
                    'PACKAGE_STATUS': body,
                    'FLAG': arrival,
                    'UPDATE_TIME': now
                }

                connection.ELK.handle_ES('hct', '新竹物流', doc, pack_no)

                if arrival == 1:
                    update(1, pack_no)
                else:
                    update(0, pack_no)

                break

            except Exception as e:
                attempts += 1
                if attempts == 3:
                    connection.mail.send_mail('新竹物流: {}, {}'.format(pack_no, e), '物流')


    @classmethod
    def worker(cls):
        while True:
            if not cls.SHARE_Q.empty():
                item = cls.SHARE_Q.get()
                cls.SHARE_Q.task_done()
                cls.parse_hct(item)
            else:
                break

    @classmethod
    def hct_main(cls):
        # a = [8443674831, 6832892964, 8703057812]
        sql_stat = ('''select [ORD_NUM], [PACKAGE_NO] from [dbo].[LOGISTIC_STATUS]
                       where [SCT_DESC] = '新竹貨運' and [PACKAGE_STATUS] = 0 ''')
        result = connection.db('AZURE').do_query(sql_stat)
        threads = []
        ### 向隊列中放入任務, 真正使用時, 應該設置為可持續的放入任務
        for task in result:
            cls.SHARE_Q.put(task)
        ### 開啟_WORKER_THREAD_NUM個線程
        for i in range(cls._WORKER_THREAD_NUM):
            thread = MyThread(cls.worker)
            thread.start() ### 線程開始處理任務
            time.sleep(0.67)
            threads.append(thread)
        for thread in threads:
            thread.join()
        ### 等待所有任務完成
        cls.SHARE_Q.join()



###黑貓### 順利送達
class t_cat(request, MyThread):

    SHARE_Q = queue.Queue()
    _WORKER_THREAD_NUM = 2

    @classmethod
    def parse_tcat(cls, item):

        # pack_no = str(item)
        pack_no = str(item[1])
        ord_num = str(item[0])

        url = "http://www.t-cat.com.tw/Inquire/TraceDetail.aspx?BillID={}&ReturnUrl=Trace.aspx".format(str(pack_no))

        ###test package_no : 905224497856, 905219336964, 905224497590
        # payload = {'__EVENTTARGET': 'ctl00$ContentPlaceHolder1$btnSend',
        #            '__VIEWSTATE': '/wEPDwULLTE2ODAyMTAzNDBkZHngR2yLNdcoB1YXtf+bAIxi/AHF',
        #            '__VIEWSTATEGENERATOR': '9A093EFF',
        #            '__EVENTVALIDATION': '/wEWDALXz8K8AwKUhrKJAQL5nJT0BgLes/beDALDytjJAgKo4bq0CAKN+JyfDgLyjv+JBAKHub7IDALsz6CzAgKUhvK7DAK97Mp+etzK3cOKerX3pzYyBL/kZYAJxkM=',
        #            'q': '站內搜尋',
        #            'cx': '005475758396817196247:vpg-mgvhr44',
        #            'cof': 'FORID:11',
        #            'ie': 'UTF-8',
        #            'ctl00$ContentPlaceHolder1$txtQuery1': str(pack_no),
        #            'ctl00$ContentPlaceHolder1$txtQuery2': '',
        #            'ctl00$ContentPlaceHolder1$txtQuery3': '',
        #            'ctl00$ContentPlaceHolder1$txtQuery4': '',
        #            'ctl00$ContentPlaceHolder1$txtQuery5': '',
        #            'ctl00$ContentPlaceHolder1$txtQuery6': '',
        #            'ctl00$ContentPlaceHolder1$txtQuery7': '',
        #            'ctl00$ContentPlaceHolder1$txtQuery8': '',
        #            'ctl00$ContentPlaceHolder1$txtQuery9': '',
        #            'ctl00$ContentPlaceHolder1$txtQuery10': ''}
        #
        # headers = {
        #     'origin': "http://www.t-cat.com.tw",
        #     'upgrade-insecure-requests': "1",
        #     'user-agent': "Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/57.0.2987.133 Safari/537.36",
        #     'content-type': "application/x-www-form-urlencoded",
        #     'accept': "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        #     'referer': "http://www.t-cat.com.tw/Inquire/trace.aspx",
        #     'accept-encoding': "gzip, deflate",
        #     'accept-language': "zh-TW,zh;q=0.8,en-US;q=0.6,en;q=0.4",
        #     'cookie': "ASP.NET_SessionId=scc5f2jtods2jfjv3v1ocl55; citrix_ns_id=aiBnezMSMEtxItV5I4rX03tU3RIA010; __utmt=1; __utma=8454064.936897360.1494375638.1494375638.1494375638.1; __utmb=8454064.1.10.1494375638; __utmc=8454064; __utmz=8454064.1494375638.1.1.utmcsr=(direct)|utmccn=(direct)|utmcmd=(none)",
        #     'cache-control': "no-cache"
        # }

        attempts = 0
        while attempts < 3:
            try:
                result = request.get_page_utf8(url)

                arrival = 0

                tcat_list = list()

                if result.find_all('td', {'class':'style1'}):
                    for i in result.find_all('td', {'class':'style1'}):
                        text = i.text.replace(' ', '')
                        tcat_list.append(text)
                        if '順利送達' in text:
                            arrival = 1
                        if text is None:
                            connection.mail.send_mail('黑貓宅急便: {}, HTML格式可能改變'.format(pack_no), '物流')
                else:
                    update(0, pack_no)
                    break

                body = [{'status': tcat_list[i],
                         'date': tcat_list[i+1][:-5] + ' ' + tcat_list[i+1][-5:],
                         'station': tcat_list[i+2],
                         'status_code': ''} for i in range(0, len(tcat_list), 3)]

                now = datetime.datetime.today().strftime("%Y-%m%d-%H:%M:%S")
                doc = {
                    'ORD_NUM': ord_num,
                    'PACKAGE_NO': pack_no,
                    'PACKAGE_STATUS': body,
                    'FLAG': arrival,
                    'UPDATE_TIME': now,
                }

                connection.ELK.handle_ES('tcat', '黑貓宅急便', doc, pack_no)

                if arrival == 1:
                    update(1, pack_no)
                else:
                    update(0, pack_no)

                break

            except Exception as e:
                attempts += 1
                if attempts == 3:
                    connection.mail.send_mail('黑貓宅急便: {}, {}'.format(pack_no, e), '物流')

    @classmethod
    def worker(cls):
        while True:
            if not cls.SHARE_Q.empty():
                item = cls.SHARE_Q.get()
                cls.parse_tcat(item)
                cls.SHARE_Q.task_done()
            else:
                break

    @classmethod
    def tcat_main(cls):
        # a = [905244040160, 905244040145]
        sql_stat = ('''select [ORD_NUM], [PACKAGE_NO] from [dbo].[LOGISTIC_STATUS]
                       where [SCT_DESC] = '統一速達(黑貓宅急便)' and [PACKAGE_STATUS] = 0 ''')
        result = connection.db('AZURE').do_query(sql_stat)
        threads = []

        for task in result:
            cls.SHARE_Q.put(task)

        for i in range(cls._WORKER_THREAD_NUM):
            thread = MyThread(cls.worker)
            # time.sleep(0.27)
            # thread.setDaemon(True)
            thread.start()
            threads.append(thread)
        for thread in threads:
            thread.join()
        cls.SHARE_Q.join()

###郵局### 投遞成功
class pstmail(MyThread):

    SHARE_Q = queue.Queue()
    _WORKER_THREAD_NUM = 2

    class pstmail_data:

        @classmethod
        def random_uuid(cls):

            pst_url = "http://postserv.post.gov.tw/pstmail/jcaptcha?uuid="
            digits = string.digits
            ascii_low = string.ascii_lowercase
            ### sample : af37b7e2-a4af-4e3d-836b-ca8b8f11c530
            # uuid_1 = ''.join(random.choice(digits + ascii_low) for _ in range(8)) + '-'
            # uuid_2 = ''.join(random.choice(digits + ascii_low) for _ in range(4)) + '-'
            # uuid_3 = ''.join(random.choice(digits + ascii_low) for _ in range(4)) + '-'
            # uuid_4 = ''.join(random.choice(digits + ascii_low) for _ in range(4)) + '-'
            uuid_5 = ''.join(random.choice(digits + ascii_low) for _ in range(12))

            uuid = 'af37b7e2-a4af-4e3d-836b-' + uuid_5
            pst_url_uuid = pst_url + uuid

            return (pst_url_uuid, uuid)

        @classmethod
        def pic_handle(cls):

            ### random create uuid and url
            data = cls.random_uuid()
            ### random create uuid and url
            pst_url = data[0]
            uuid = data[1]

            pic_path = 'C:\\Users\\kevin_huang\\Logistic_Parse\\pic\\'
            pic_name = str(uuid) + '.png'

            def pic_request():

                def pic_save(data, fn):

                    sizes = np.shape(data)
                    height = float(sizes[0])
                    width = float(sizes[1])
                    fig = plt.figure()
                    fig.set_size_inches(width / height, 1, forward=False)
                    ax = plt.Axes(fig, [0., 0., 1., 1.])
                    ax.set_axis_off()
                    fig.add_axes(ax)
                    ax.imshow(data)
                    plt.savefig(fn, dpi=300)
                    plt.close()

                response = requests.get(pst_url)
                img = Image.open(BytesIO(response.content))
                # img.save('C:\\Users\\kevin_huang\\Logistic_Parse\\pic\\haha.jpg', quality=95)
                THRESHOLD_VALUE = 40
                # img = Image.open("C:\\Users\\kevin_huang\\Logistic_Parse\\pic\\haha.jpg")
                img = img.convert("L")
                img = img.resize((150, 50), Image.ANTIALIAS)
                imgData = np.asarray(img)
                thresholdedData = (imgData > THRESHOLD_VALUE) * 5000000

                pic_save(thresholdedData, pic_path + pic_name)

            def pic_OCR():

                # image_path = 'C:\\Users\\kevin_huang\\Logistic_Parse\\pic\\'

                clean_result = str()

                while len(clean_result) != 4:
                    ### exec pic_request ###
                    pic_request()
                    ### exec pic_request ###
                    # png_files = [f for f in os.listdir(pic_path) if f.endswith('.png')][0]
                    image_png = Image.open(os.path.join(pic_path, pic_name))
                    dirty_result = pytesseract.image_to_string(image_png, config='digits')
                    clean_result = dirty_result.replace(' ','').replace('.','').replace('-','')
                    # os.remove(pic_path + pic_name)

                return clean_result

            return uuid, pic_OCR()



    @classmethod
    def parse_pst(cls, item):

        # pack_no = str(item)
        pack_no = str(item[1])
        ord_num = str(item[0])

        url = "http://postserv.post.gov.tw/pstmail/EsoafDispatcher"

        # data = pstmail.pstmail_data.pic_handle()
        # uuid = data[0]
        # captcha = data[1]

        ### 5 個 mail_info 參數，UUID，CAPCHA
        # payload = """{"header":{"InputVOClass":"com.systex.jbranch.app.server.post.vo.EB500100InputVO",
        #                         "TxnCode":"EB500100","BizCode":"query","StampTime":true,"SupvPwd":"",
        #                         "TXN_DATA":{},"SupvID":"","CustID":"","REQUEST_ID":"","ClientTransaction":true,
        #                         "DevMode":false,"SectionID":"esoaf"},
        #               "body":{"MAILNO1":""" + "'" + str(pack_no) + "'" + """,
        #                       "MAILNO2":"",
        #                       "MAILNO3":"",
        #                       "MAILNO4":"",
        #                       "MAILNO5":"",
        #                       "uuid":""" + "'" + str(uuid) + "'" + """,
        #                       "captcha":""" + "'" + str(captcha) + "'" + """,
        #                       "pageCount":10}}"""

        payload = """{"header":
                        {"InputVOClass":"com.systex.jbranch.app.server.post.vo.EB500100InputVO",
                         "TxnCode":"EB500100","BizCode":"query2","StampTime":true,"SupvPwd":"",
                         "TXN_DATA":{},"SupvID":"","CustID":"","REQUEST_ID":"","ClientTransaction":true,
                         "DevMode":false,"SectionID":"esoaf"},
                      "body":{"MAILNO":""" + "'" + pack_no + "'" + ""","pageCount":10}}"""
        headers = {
            'accept': "application/json, text/plain, */*",
            'origin': "http://postserv.post.gov.tw",
            'user-agent': "Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/57.0.2987.133 Safari/537.36",
            'content-type': "application/json;charset=UTF-8",
            'referer': "http://postserv.post.gov.tw/pstmail/main_mail.html",
            'accept-encoding': "gzip, deflate",
            'accept-language': "zh-TW,zh;q=0.8,en-US;q=0.6,en;q=0.4",
            'cache-control': "no-cache"
        }

        attempts = 0
        while attempts < 3:
            try:
                response = requests.request("POST", url, data=payload, headers=headers)
                response_text = response.text.replace('[', '').replace(']', '').replace(' ','').replace('\u3000', '')

                if '無此資料' in response_text or not response_text:
                    update(0, pack_no)
                    break

                pattern = 'DATIME\":\".*?\"|STATUS\":\".*?\"|BRHNC\":\".*?\"'
                result = re.findall(pattern, response_text)[1:]

                ### verify 'DATIME":""' in result or not ###
                # if 'DATIME":""' in result:
                #     result.remove('DATIME":""')
                for i in result:
                    if i == 'DATIME":""':
                        result.remove(i)
                ### verify 'DATIME":""' in result or not ###

                clean_1 = list()
                arrival = 0

                if result:
                    for i in result:
                        text = i.replace('"', '').replace('BRHNC', 'station').replace('DATIME', 'date').replace('STATUS', 'status')
                        clean_1.append(text)
                        if '投遞成功' in text:
                            arrival = 1
                    # clean_1 = [i.replace('"', '').replace('BRHNC', '處理單位').replace('DATIME', '處理日期時間').replace('STATUS', '目前狀態') for i in result]
                    clean_2 = [[clean_1[i], clean_1[i + 1], clean_1[i + 2]] for i in range(0, len(clean_1), 3)]

                    body = [{clean_2[i][0].split(':')[0]: clean_2[i][0].split(':')[1],
                             clean_2[i][1].split(':')[0]: clean_2[i][1].split(':')[1],
                             clean_2[i][2].split(':')[0]: clean_2[i][2].split(':')[1],
                             'status_code': ''} for i in range(0, len(clean_2))]

                    now = datetime.datetime.today().strftime("%Y-%m%d-%H:%M:%S")

                    doc = {
                        'ORD_NUM': ord_num,
                        'PACKAGE_NO': pack_no,
                        'PACKAGE_STATUS': body,
                        'FLAG': arrival,
                        'UPDATE_TIME': now,
                    }
                    connection.ELK.handle_ES('pstmail', '郵局', doc, pack_no)

                    if arrival == 1:
                        update(1, pack_no)
                    else:
                        update(0, pack_no)

                    break

                else:
                    attempts += 1
                    time.sleep(300)
                    if attempts == 2:
                        connection.mail.send_mail('郵局: {}, JSON格式可能改變'.format(pack_no), '物流')

            except Exception as e:
                attempts += 1
                if attempts == 2:
                    connection.mail.send_mail('郵局: {}, {}'.format(pack_no, e), '物流')

    @classmethod
    def worker(cls):
        while True:
            if not cls.SHARE_Q.empty():
                item = cls.SHARE_Q.get()
                cls.parse_pst(item)
                cls.SHARE_Q.task_done()
            else:
                break

    @classmethod
    def pstmail_main(cls):

        # a = ['00898360203218', '00487830300816']
        sql_stat = ('''select [ORD_NUM], [PACKAGE_NO] from [dbo].[LOGISTIC_STATUS]
                       where [SCT_DESC] = '郵局' and [PACKAGE_STATUS] = 0 ''')
        result = connection.db('AZURE').do_query(sql_stat)

        threads = []

        for task in result:
            cls.SHARE_Q.put(task)

        for i in range(cls._WORKER_THREAD_NUM):
            thread = MyThread(cls.worker)
            # time.sleep(0.37)
            # thread.setDaemon(True)
            thread.start()
            # thread.join()
            threads.append(thread)
        for thread in threads:
            thread.join()
        cls.SHARE_Q.join()


###宅配通###	配送完成
class e_can(request, MyThread):

    SHARE_Q = queue.Queue()
    _WORKER_THREAD_NUM = 1
    ip_block = 0

    @classmethod
    def parse_ecan(cls, item):

        # pack_no = str(item)
        pack_no = str(item[1])
        ord_num = str(item[0])

        # url1 = 'http://query2.e-can.com.tw/%E5%A4%9A%E7%AD%86%E6%9F%A5%E4%BB%B6_oo4o.asp'
        url2 = 'http://query2.e-can.com.tw/self_link/id_link_c.asp?txtMainid={}'.format(pack_no)

        # data = {'txtMainID_1':str(pack_no),
        #         'txtMainID_6':'',
        #         'txtMainID_2':'',
        #         'txtMainID_7':'',
        #         'txtMainID_3':'',
        #         'txtMainID_8':'',
        #         'txtMainID_4':'',
        #         'txtMainID_9':'',
        #         'txtMainID_5':'',
        #         'txtMainID_10':'',
        #         'B1':'(unable to decode value)'}

        # s = requests.Session()
        # response = s.post(url=url1, data=data)

        headers = {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
            "Accept-Encoding": "gzip, deflate",
            "Accept-Language": "zh-TW,zh;q=0.8,en-US;q=0.6,en;q=0.4",
            "Cache-Control": "max-age=0",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Host": "query2.e-can.com.tw",
            "Referer": "http://query2.e-can.com.tw/%E5%A4%9A%E7%AD%86%E6%9F%A5%E4%BB%B6_oo4o.asp"
            # "X-Forwarded-For": request.random_ip()
            # "REMOTE_ADDR": request.random_ip()
        }

        attempts = 0
        while attempts < 3:
            try:
                result = request.get_page_utf8(url=url2, request_header=headers)
                # result = s.get(url=url2, headers=headers)

                ### hinet判斷 ###
                if result.find('img', {'alt': 'HiNet連線速率測試'}):
                    # connection.mail.send_mail('宅配通: {}, IP被檔'.format(pack_no), '物流')
                    cls.ip_block = 1
                    break
                ### hinet判斷 ###

                ecan_list = list()
                arrival = 0

                remove_list = ['宅配單號', '貨物狀態', '說明',
                               '日期 / 時間', '作業站']

                if result.find_all('div', {'align': 'center'}):
                    for i in result.find_all('div', {'align': 'center'}):
                        if i.text not in remove_list:
                            text = i.text.replace('\n', '')
                            ecan_list.append(text)
                            if '配送完成' == text or '貨件送達' == text:
                                arrival = 1
                            if text is None:
                                connection.mail.send_mail('宅配通: {}, HTML格式可能改變'.format(pack_no), '物流')

                else:
                    update(0, pack_no)
                    break

                body = [{'status': ecan_list[i+1],
                         'date': ecan_list[i+3],
                         'station': ecan_list[i+4] + '營業所',
                         'status_code': ''} for i in range(0, len(ecan_list), 5)]

                now = datetime.datetime.today().strftime("%Y-%m%d-%H:%M:%S")

                doc = {
                    'ORD_NUM': ord_num,
                    'PACKAGE_NO': pack_no,
                    'PACKAGE_STATUS': body,
                    'FLAG': arrival,
                    'UPDATE_TIME': now
                }

                connection.ELK.handle_ES('ecan', '宅配通', doc, pack_no)

                if arrival == 1:
                    update(1, pack_no)
                else:
                    update(0, pack_no)

                break

            except Exception as e:
                attempts += 1
                if attempts == 3:
                    connection.mail.send_mail('宅配通: {}, {}'.format(pack_no, e), '物流')

    @classmethod
    def worker(cls):

        count = 0
        while True:
            while not cls.SHARE_Q.empty():
                count += 1
                if count > 80:
                    count = 0
                    time.sleep(105)
                # 被擋的話，清空queue，讓queue.get == False
                if cls.ip_block == 1:
                    connection.mail.send_mail('宅配通: IP被檔', '物流')
                    cls.SHARE_Q = queue.Queue()
                else:
                    item = cls.SHARE_Q.get()
                    cls.parse_ecan(item)
                    cls.SHARE_Q.task_done()
            else:
                break

    @classmethod
    def ecan_main(cls):

        # a = [778014468840, 777039297694, 777039300520]

        sql_stat = ('''select [ORD_NUM], [PACKAGE_NO] from [dbo].[LOGISTIC_STATUS]
                       where [SCT_DESC] = '台灣宅配通' and [PACKAGE_STATUS] = 0 ''') # and [PACKAGE_STATUS] = 0  and [package_no] = '777060026116'
        result = connection.db('AZURE').do_query(sql_stat)

        threads = []

        for task in result:
            cls.SHARE_Q.put(task)

        for i in range(cls._WORKER_THREAD_NUM):
            thread = MyThread(cls.worker)
            thread.start()
            threads.append(thread)
        for thread in threads:
            thread.join()
        cls.SHARE_Q.join()


###嘉里###配達,已完成簽收
class ktj(request, MyThread):

    SHARE_Q = queue.Queue()
    _WORKER_THREAD_NUM = 2

    @classmethod
    def parse_ktj(cls, item):

        # pack_no = str(item)
        pack_no = str(item[1])
        ord_num = str(item[0])

        url = 'https://www.kerrytj.com/ZH/search/table_list.aspx'
        data = {'gno': pack_no}
        header = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Origin": "https://www.kerrytj.com",
            "Referer": "https://www.kerrytj.com/zh/search/search_track.aspx",
            "Upgrade-Insecure-Requests": "1"
        }
        # url = 'https://www.kerrytj.com/zh/search/search_track_list.aspx'
        # data = {
        #     'rdType': '0',
        #     'trackNo1': str(pack_no),
        #     'trackNo2': '',
        #     'trackNo3': '',
        #     'trackNo4': '',
        #     'trackNo5': '',
        #     'btnTrack': 'Submit'
        # }
        attempts = 0
        while attempts < 3:
            try:
                result = request.get_page_utf8(url, request_header=header, parameters=data)

                ktj_list = list()
                arrival = 0

                if result.find_all('td', {'align': 'left'}):
                    for i in result.find_all('td', {'align': 'left'}):
                        ktj_list.append(i.text)
                        if '已完成簽收' in i.text:
                            arrival = 1
                        if i.text is None:
                            connection.mail.send_mail('嘉里物流: {}, HTML格式可能改變'.format(pack_no), '物流')
                else:
                    update(0, pack_no)
                    break

                body = [{'date': ktj_list[i] + ' ' + ktj_list[i+1],
                         'status': ktj_list[i+2],
                         'station': ktj_list[i+3] + '營業所',
                         'status_code': ''} for i in range(0, len(ktj_list), 4)]

                now = datetime.datetime.today().strftime("%Y-%m%d-%H:%M:%S")

                doc = {
                    'ORD_NUM': ord_num,
                    'PACKAGE_NO': pack_no,
                    'PACKAGE_STATUS': body,
                    'FLAG': arrival,
                    'UPDATE_TIME': now
                }

                connection.ELK.handle_ES('ktj', '嘉里物流', doc, str(pack_no))

                if arrival == 1:
                    update(1, pack_no)
                else:
                    update(0, pack_no)

                break

            except Exception as e:
                attempts += 1
                if attempts == 3:
                    connection.mail.send_mail('嘉里物流: {}, {}'.format(pack_no, e), '物流')


    @classmethod
    def worker(cls):
        while True:
            if not cls.SHARE_Q.empty():
                item = cls.SHARE_Q.get()
                cls.parse_ktj(item)
                cls.SHARE_Q.task_done()
            else:
                break

    @classmethod
    def ktj_main(cls):

        # a = ['92495261821']

        sql_stat = ('''select [ORD_NUM], [PACKAGE_NO] from [dbo].[LOGISTIC_STATUS]
                       where [SCT_DESC] = '嘉里大榮物流' and [PACKAGE_STATUS] = 0 ''')
        result = connection.db('AZURE').do_query(sql_stat)
        threads = []

        for task in result:
            cls.SHARE_Q.put(task)

        for i in range(cls._WORKER_THREAD_NUM):
            thread = MyThread(cls.worker)
            # time.sleep(0.27)
            # thread.setDaemon(True)
            thread.start()
            threads.append(thread)
        for thread in threads:
            thread.join()

        cls.SHARE_Q.join()



###通盈通運###已送達
class tong_ying(request, MyThread):

    SHARE_Q = queue.Queue()
    _WORKER_THREAD_NUM = 2

    @classmethod
    def parse_tongying(cls, item):

        # pack_no = str(item)
        pack_no = str(item[1])
        ord_num = str(item[0])

        url = 'http://www.tong-ying.com.tw/exploitation/sw.php?on1='
        url2 = 'http://www.tong-ying.com.tw/exploitation/search2.php'

        payload = {
            'on1': pack_no,
            'on2': '',
            'on3': ''
        }

        attempts = 0
        while attempts < 3:
            try:
                result = request.get_page_utf8(url=url+pack_no)
                result2 = request.get_page_utf8(url=url2, parameters=payload)
                ###發送日期	發送站	貨物條碼	收件人	送達日期	代收款	訂單編號	配送狀態###
                tongying_list = list()
                tongying_list2 = list()
                arrival = 0

                remove_list = ['點貨日期', '作業別', '件數', '才數', '作業站所', '車番', '配送狀態',
                               '發送日期', '發送站', '配送編號', '寄件人', '收件人', '送達日期',
                               '訂單編號', '配送狀態', '配送狀況', 'Payeasy             ', ' ']

                if result.find_all('div', {'align':'center', 'class': 'style2'} ):
                    for i in result.find_all('div', {'align':'center', 'class': 'style2'} ):
                        if i.text not in remove_list:
                            text = i.text.replace(' ', '')
                            tongying_list.append(text)
                            # if '已送達' in text:
                            #     arrival = 1
                            if text is None:
                                connection.mail.send_mail('通盈貨運: {}, HTML格式可能改變'.format(pack_no), '物流')
                    for j in result2.find_all('font', {'color': 'white'}):
                        if j.text not in remove_list:
                            text2 = j.text.replace(' ','')
                            tongying_list2.append(text2)
                        if '已送達' in tongying_list2:
                            arrival = 1
                else:
                    update(0, pack_no)
                    break

                # body = [{'點貨日期': tongying_list[i],
                #          '作業別': tongying_list[i + 1],
                #          '件數': tongying_list[i + 2],
                #          '才數': tongying_list[i + 3],
                #          '作業站所': tongying_list[i + 4],
                #          '車番': tongying_list[i + 5]} for i in range(0, len(tongying_list), 6)]

                body = [{'date': tongying_list[i],
                         'status': tongying_list[i + 1],
                         'station': tongying_list[i + 4].replace('站', '營業所'),
                         'status_code': ''} for i in range(0, len(tongying_list), 6)]

                if arrival == 1:
                    body.append({'date': tongying_list2[-2],
                                 'status': tongying_list2[-1],
                                 'station': body[len(body) - 1].get('業所'),
                                 'status_code': ''}) #len(body) - 1 判斷通盈有幾個結果

                now = datetime.datetime.today().strftime("%Y-%m%d-%H:%M:%S")

                doc = {
                    'ORD_NUM': ord_num,
                    'PACKAGE_NO': pack_no,
                    'PACKAGE_STATUS': body,
                    'FLAG': arrival,
                    'UPDATE_TIME': now
                }

                connection.ELK.handle_ES('tongyin', '通盈貨運', doc, str(pack_no))

                if arrival == 1:
                    update(1, pack_no)
                else:
                    update(0, pack_no)

                break

            except Exception as e:
                attempts += 1
                if attempts == 3:
                    connection.mail.send_mail('通盈貨運: {}, {}'.format(pack_no, e), '物流')
                    # connection.mail.send_mail('通盈貨運: {}, {}'.format(pack_no, sys.exc_info()[-1].tb_lineno), '物流')

    @classmethod
    def worker(cls):
        while True:
            if not cls.SHARE_Q.empty():
                item = cls.SHARE_Q.get()
                cls.parse_tongying(item)
                cls.SHARE_Q.task_done()
            else:
                break

    @classmethod
    def tongying_main(cls):

        # a = [7272432870]
        sql_stat = ('''select [ORD_NUM], [PACKAGE_NO] from [dbo].[LOGISTIC_STATUS]
                       where [SCT_DESC] = '通盈通運' and [PACKAGE_STATUS] = 0 ''')
        result = connection.db('AZURE').do_query(sql_stat)
        threads = []

        for task in result:
            cls.SHARE_Q.put(task)

        for i in range(cls._WORKER_THREAD_NUM):
            thread = MyThread(cls.worker)
            # time.sleep(0.27)
            # thread.setDaemon(True)
            thread.start()
            threads.append(thread)
        for thread in threads:
            thread.join()

        cls.SHARE_Q.join()

###便利帶###送件完成
class maple(request, MyThread):

    SHARE_Q = queue.Queue()
    _WORKER_THREAD_NUM = 2

    @classmethod
    def parse_maple(cls, item):

        # pack_no = str(item)
        pack_no = str(item[1])
        ord_num = str(item[0])

        ##查無條碼(6週)
        url = 'http://www.25431010.tw/Search.php'

        s = requests.Session()
        response = s.get(url)

        result = BeautifulSoup(response.text, 'lxml')

        payload = {
            'tik': result.find('input', {'name': 'tik'})['value'],
            'BARCODE1': pack_no,
            'BARCODE2': '',
            'BARCODE3': ''
        }

        headers = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Encoding': 'gzip, deflate',
            'Accept-Language': 'zh-TW,zh;q=0.8,en-US;q=0.6,en;q=0.4',
            'Cache-Control': 'max-age=0',
            'Connection': 'keep-alive',
            'Content-Length': '65',
            'Content-Type': 'application/x-www-form-urlencoded',
            'Host': 'www.25431010.tw',
            'Origin': 'http://www.25431010.tw',
            'Referer': 'http://www.25431010.tw/Search.php',
            'Upgrade-Insecure-Requests': '1',
            'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36',
            'Cookie': response.headers.get('Set-Cookie').replace('; path=/; HttpOnly', '')
        }

        attempts = 0
        response2 = None
        while attempts < 3:
            try:
                req_counts = 0
                while req_counts < 3:
                    response2 = s.post(url, data=payload, headers=headers)
                    if response2.status_code == 200:
                        break
                    else:
                        req_counts += 1

                if req_counts == 3:
                    connection.mail.send_mail('便利帶: status code != 200', '物流')
                    threading.Event().is_set()

                result2 = BeautifulSoup(response2.text, 'lxml')

                # tik_html = request.get_page_utf8(url)
                # tik_values = None
                # for i in tik_html.find_all('input', {'name': 'tik'}):
                #     tik_values = i['value']
                # # print(tik_values)
                #
                # data = {
                #     'tik':tik_values,
                #     'BARCODE1':'',
                #     'BARCODE2':str(pack_no),
                #     'BARCODE3':''
                # }
                #
                # result = request.get_page_utf8(url, data)

                maple_list = list()
                arrival = 0
                remove_list = ['配送歷程', '條碼1', '日期', '目前狀態']
                # 查無條碼
                # if result2.find_all('td', {'align': 'center', 'bgcolor': '#FFFFCC'}):
                    # for i in result2.find_all('td', {'align': 'center', 'bgcolor': '#FFFFCC'}):
                if result2.find_all('td', {'align': 'center', 'valign': 'top'}):
                    for i in result2.find_all('td', {'align': 'center', 'valign': 'top'}):
                        text = i.text.replace('\xa0', '')
                        if text not in remove_list and 1 < len(text) <= 12:
                            maple_list.append(text)
                            if '送件完成' in text:
                                arrival = 1
                            if text is None:
                                connection.mail.send_mail('便利帶: {}, HTML格式可能改變'.format(pack_no), '物流')
                else:
                    update(0, pack_no)
                    break

                # body = [{'條碼': maple_list[i],
                #          '日期': maple_list[i + 1],
                #          '目前狀態': maple_list[i + 2]} for i in range(0, len(maple_list), 3)]

                ### 把前面3個拿掉，如果委外的話，狀態結束 ###
                """if '委外' in maple_list:
                    arrival = 1
                    maple_list = maple_list[6:]
                else:
                    maple_list = maple_list[3:]"""
                for i in maple_list:
                    if '*' in i:
                        arrival = 1
                        del maple_list[3:6]

                if '委外' in maple_list:
                    arrival = 1
                    maple_list = maple_list[6:]
                else:
                    maple_list = maple_list[3:]
                ### 把前面3個拿掉，如果委外的話，狀態結束###

                body = [{'station': '',
                         'date': maple_list[i + 1],
                         'status': maple_list[i + 2],
                         'status_code': ''} for i in range(0, len(maple_list), 3)]

                now = datetime.datetime.today().strftime("%Y-%m%d-%H:%M:%S")

                doc = {
                    'ORD_NUM': ord_num,
                    'PACKAGE_NO': pack_no,
                    'PACKAGE_STATUS': body,
                    'FLAG': arrival,
                    'UPDATE_TIME': now
                }

                connection.ELK.handle_ES('maple', '便利帶', doc, str(pack_no))

                if arrival == 1:
                    update(1, pack_no)
                else:
                    update(0, pack_no)

                break

            except Exception as e:
                attempts += 1
                if attempts == 3:
                    connection.mail.send_mail('便利帶: {}, {}'.format(pack_no, e), '物流')

    @classmethod
    def worker(cls):
        while True:
            if not cls.SHARE_Q.empty():
                item = cls.SHARE_Q.get()
                cls.parse_maple(item)
                cls.SHARE_Q.task_done()
            else:
                break

    @classmethod
    def maple_main(cls):

        # a = ['010145523083']
        sql_stat = ('''select [ORD_NUM], [PACKAGE_NO] from [dbo].[LOGISTIC_STATUS]
                       where [SCT_DESC] = '豐業物流(便利帶)' and [PACKAGE_STATUS] = 0 ''') #
        result = connection.db('AZURE').do_query(sql_stat)
        threads = []

        for task in result:
            cls.SHARE_Q.put(task)

        for i in range(cls._WORKER_THREAD_NUM):
            thread = MyThread(cls.worker)
            thread.start()
            time.sleep(0.3)
            threads.append(thread)
        for thread in threads:
            thread.join()

        cls.SHARE_Q.join()

def update(status, pack_no):

    sql_stat = ('''update [dbo].[LOGISTIC_STATUS]
                   set [PACKAGE_STATUS] = %s, [PARSE_DATE] = CONVERT(VARCHAR(19), GETDATE(), 120)
                   where [PACKAGE_NO] = %s''')
    connection.db('AZURE').do_query(sql_stat, (status, str(pack_no)))


def main():

    SHARE_Q = queue.Queue()
    _WORKER_THREAD_NUM = 4

    def worker():

        while True:
            if not SHARE_Q.empty():
                item = SHARE_Q.get()
                item()
                SHARE_Q.task_done()
            else:
                break

    def start():

        ### put method into list
        a = [e_can.ecan_main, hct.hct_main, t_cat.tcat_main, pstmail.pstmail_main,
             ktj.ktj_main, maple.maple_main, tong_ying.tongying_main]
        # a = [hct.hct_main, t_cat.tcat_main, pstmail.pstmail_main,
        #      ktj.ktj_main, maple.maple_main, tong_ying.tongying_main]
        # a = [hct.hct_main, pstmail.pstmail_main]
        threads = []

        for task in a:
            SHARE_Q.put(task)

        for i in range(_WORKER_THREAD_NUM):
            thread = MyThread(worker)
            # thread.setDaemon(True)
            thread.start()
            threads.append(thread)
        for thread in threads:
            thread.join()

        SHARE_Q.join()

    start()

if __name__ == '__main__':

    main()
    print('Finish')
    # sys.exit()

