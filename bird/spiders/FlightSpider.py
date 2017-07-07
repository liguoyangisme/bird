# -*- coding: utf-8 -*-
import scrapy
import json
from urllib import quote
import time

import sys
from items import FlightItem

# 航班价格爬虫
from utils.DateUtils import DateUtils
from pymongo import MongoClient

reload(sys)
sys.setdefaultencoding('utf-8')

class FlightSpider(scrapy.spiders.Spider):
    name = "flight"
    allowed_domains = ["flights.ctrip.com"]

    # 开始方法
    def start_requests(self):
        # 读取航线列表
        file = open("datas/line_min.json")
        # 转换航线列表
        lines = json.load(file)

        # return [scrapy.Request(
        #     "http://flights.ctrip.com/Domestic/Search/FirstRoute/?DDate1=2017-07-08&DCityName1=%s&ACityName1=%s" % (
        #         quote(u"北京".encode("gb2312")), quote(u"大连".encode("gb2312"))),
        #     callback=self.list_parse
        # )]

        # 机票列表页面
        for line in lines:
            for date in self.rangeDate():
                yield scrapy.Request(
                    "http://flights.ctrip.com/Domestic/Search/FirstRoute/?DDate1=%s&DCityName1=%s&ACityName1=%s" % (
                        # 出发日期，出发城市，到达城市
                        date, quote(line["fromCity"].encode("gb2312")), quote(line["toCity"].encode("gb2312"))
                    ),
                    callback=self.list_parse
                )

    # 提取JSON_URL
    def list_parse(self, response):
        # 提取JSON的URL
        json_url = 'http:' + response.selector.re('var\surl\s=\s\"(.+)\"')[0]
        return scrapy.Request(json_url, callback=self.json_parse)

    # 提取JSON
    def json_parse(self, response):

        # 解析JSON
        data = json.loads(response.body, encoding='gb2312')

        def filter_around(filght):
            return filght['xpsm'] == 0

        # Mongo连接
        client = MongoClient("localhost", 27018)
        db = client.bird
        collection = db.flight
        if data['fis'].__len__() == 0:
            print "返回空 %s" % response.meta["proxy"]
            return scrapy.Request(
                    response.url
                    ,
                    callback=self.list_parse
                )
        else:
            print "返回正常 %s" % response.meta["proxy"]

        # 过滤出发地周边航班
        for fl in filter(filter_around, data['fis']):
            item = FlightItem()
            # 爬取时间
            item['findDate'] = DateUtils().todayStr()
            item['findTime'] = DateUtils().nowStr()
            # 爬取渠道
            item['source'] = "ctrip"

            # 出发城市
            item['fromCity'] = fl['dcn']
            # 出发城市编号
            item['fromCityCode'] = fl['dcc']
            # 出发机场
            item['fromAir'] = fl['dpbn']
            # 出发机场编号
            item['fromAirCode'] = fl['dpc']
            # 出发机场航站楼
            item['fromAirNo'] = fl['dsmsn']

            # 到达城市
            item['toCity'] = fl['acn']
            # 到达城市编号
            item['toCityCode'] = fl['acc']
            # 到达机场
            item['toAir'] = fl['apbn']
            # 到达机场编号
            item['toAirCode'] = fl['apc']
            # 到达机场航站楼
            item['toAirNo'] = fl['asmsn']

            # 航空公司
            item['air'] = fl['alc']
            # 航班号
            item['number'] = fl['fn']
            # 出发日期
            item['fromDate'] = fl['dt'][0:10]
            # 出发时间
            item['fromTime'] = fl['dt']
            # 达到时间
            item['toTime'] = fl['at']

            # 价格
            item['price'] = fl['lp']
            # 原价
            item['basePrice'] = fl['lcfp']
            # 机场建设费
            item['tax'] = fl['tax']

            collection.insert(item)
            # yield item

    # 未来90天内日期列表
    def rangeDate(self):
        return [DateUtils().addDayStr(days) for days in range(1,91)]
