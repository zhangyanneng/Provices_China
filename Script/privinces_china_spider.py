#!/usr/bin/python
# -*- coding: utf-8 -*-

#python的str默认是ascii编码，和unicode编码冲突
import sys
reload(sys)
sys.setdefaultencoding('utf8')
import scrapy
from scrapy.selector import Selector
from scrapy.crawler import CrawlerProcess
from biplist import *
import time
import json

class provicecitysSpider(scrapy.Spider):
    name = "provices_spider"
    allowed_domains = ["www.stats.gov.cn"]
    start_urls = [
        "http://www.stats.gov.cn/tjsj/tjbz/tjyqhdmhcxhfdm/2018/index.html",
    ]

    baseURL = "http://www.stats.gov.cn/tjsj/tjbz/tjyqhdmhcxhfdm/2018/"

    plist_file = []

    province_list = []
    city_list = []
    area_list = []


    def parse(self, response):
        papers = response.xpath('.//table[@class="provincetable"]')
        table = papers[0]

        ttables = table.xpath('.//tr[@class="provincetr"]')

        for tr in ttables:

            hrefs = tr.xpath('.//a')

            for a in hrefs:

                p_href = a.xpath('.//@href').extract()[0]
                p_province = a.xpath('.//text()').extract()[0]

                p_code = p_href.split('.')[0]
                p_code = p_code + "0000000000"

                p_href =  self.baseURL + p_href

                # print p_href
                # print p_province

                proDict = {'code':p_code,'name':p_province,'citys':[]}
                
                # {'id': '110000', 'value': '北京市', 'parentId': '0'},
                h5_dict = {'id':p_code,'value':p_province,'parentId':'0'}
                #加入缓存
                self.plist_file.append(proDict)
                self.province_list.append(h5_dict)

                request = scrapy.Request(url= p_href,callback=self.parse_province)
                request.meta['province'] = p_province
                request.meta['provinceDict'] = proDict
                yield request

                pass
    
    #解析省份
    def parse_province(self, response):

        papers = response.xpath('.//table[@class="citytable"]')
        table = papers[0]
        trs = table.xpath('.//tr[@class="citytr"]')

        # company_list = []
        province = response.meta['province']
        provinceDict = response.meta['provinceDict']

        for tr in trs:
            tds = tr.xpath('.//td')

            a_href = tds[0].xpath('.//a/@href').extract()[0]
            a_code = tds[0].xpath('.//a/text()').extract()[0]
            a_name = tds[1].xpath('.//a/text()').extract()[0]

             #标记省份序号
            a_href_no = a_href.split('/')[0]

            a_href = self.baseURL + a_href
            # print a_href

            citys = provinceDict['citys']
            city_dict = {
                        'code':a_code,
                        'name':a_name,
                        'areas':[]
                        }
            citys.append(city_dict)

            request = scrapy.Request(url= a_href,callback=self.parse_city)
            request.meta['province'] = province
            request.meta['code'] = a_code
            request.meta['city'] = a_name
            request.meta['href_no'] = a_href_no
            request.meta['city_dict'] = city_dict
            yield request

        pass

    #解析城市
    def parse_city(self,response):
         
        papers = response.xpath('.//table[@class="countytable"]')
        table = papers[0]
        trs = table.xpath('.//tr[@class="countytr"]')

        city_dict = response.meta['city_dict']
        href_no = response.meta['href_no']
        # city = response.meta['city']
        # province = response.meta['province']

        areas = city_dict['areas']

        for tr in trs:
            tds = tr.xpath('.//td')

            if tds[0].xpath('.//a').extract():
                a_href = tds[0].xpath('.//a/@href').extract()[0]
                a_code = tds[0].xpath('.//a/text()').extract()[0]
                a_name = tds[1].xpath('.//a/text()').extract()[0]
                
                next_href_no = href_no + '/' + a_href.split('/')[0]

                a_href = self.baseURL + href_no + '/' + a_href
                # print a_href

                area_dict = {'code':a_code,'name':a_name,'streets':[]}
                areas.append(area_dict)

                request = scrapy.Request(url= a_href,callback=self.parse_area)
                # request.meta['province'] = province
                request.meta['code'] = a_code
                request.meta['city'] = a_name
                request.meta['area_dict'] = area_dict
                request.meta['href_no'] = next_href_no
                yield request
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                           
        pass

    #解析区域
    def parse_area(self,response):
        
        papers = response.xpath('.//table[@class="towntable"]')
        table = papers[0]
        trs = table.xpath('.//tr[@class="towntr"]')

        area_dict = response.meta['area_dict']
        href_no = response.meta['href_no']

        streets = area_dict['streets']

        for tr in trs:
            tds = tr.xpath('.//td')
            if tds[0].xpath('.//a').extract():
                a_href = tds[0].xpath('.//a/@href').extract()[0]
                a_code = tds[0].xpath('.//a/text()').extract()[0]
                a_name = tds[1].xpath('.//a/text()').extract()[0]

                # next_href_no = href_no + '/' + a_href.split('/')[0]

                a_href = self.baseURL + href_no + '/' + a_href

                street_dict = {'code':a_code,'name':a_name,'villages':[]}
                streets.append(street_dict)

                #抓取到村的数据时间太长了，需要话费12小时以上，大约4～5万页面
                # request = scrapy.Request(url= a_href,callback=self.parse_street)
                # request.meta['href_no'] = next_href_no
                # request.meta['street_dict'] = street_dict
                # yield request

                pass
            pass

        pass

    def parse_street(self, response):
        papers = response.xpath('.//table[@class="villagetable"]')
        table = papers[0]
        trs = table.xpath('.//tr[@class="villagetr"]')

        street_dict = response.meta['street_dict']
        villages = street_dict['villages']

        for tr in trs:
            tds = tr.xpath('.//td')
            v_code = tds[0].xpath('.//text()').extract()[0]
            v_classCode = tds[1].xpath('.//text()').extract()[0]
            v_name = tds[2].xpath('.//text()').extract()[0]

            village_dict = {'code':v_code,'name':v_name,'classCode':v_classCode}
            villages.append(village_dict)
            pass

        pass

    def write_file(self):
        try:
            #iOS
            writePlist(self.plist_file,"/Users/zyn/Desktop/provicecitys.plist")

            #android
            JsonStr = json.dumps(self.plist_file, ensure_ascii=False, encoding='UTF-8') 
            with open('/Users/zyn/Desktop/provicecitys.json','w') as json_file:
                json_file.write(JsonStr)

        except (InvalidPlistException,NotBinaryPlistException), e:
            print "Something bad happened:",e
        else:
            pass
        finally:
            pass
        pass

    def write_DB(self):
        pass


    def close(self, reason):
        #将文件写入plist文件
        print "最后执行的方法"

        self.write_file()

    pass

    


