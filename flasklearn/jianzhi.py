__author__ = "zhuangjie"

import requests
from lxml import html, etree
import re


class JianZhi(object):
    _DOMAIN = 'http://www.doumi.com'
    _CITY = 'http://www.doumi.com/cityselect/'

    def __init__(self, city, district):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.132 Safari/537.36',
            'Referer': 'http://www.doumi.com/cityselect/'
        }
        self.sess = requests.session()
        # self.location = location
        self.city = city
        self.district = district

    def get_jobs(self):
        # city, district = self.get_region()
        city = self.city
        district = self.district

        city_list, city_dict = self.get_all_citys()
        if city.endswith('市'):
            city = city[:-1]
        if city in city_list:
            url = city_dict[city]
            resp = self.sess.get(url, headers=self.headers).text
            tree = html.fromstring(resp)
            region_list = tree.xpath('//div[@class="inner-wrap"]/dl[2]/dd/ul/li')
            for region in region_list[1:]:
                region_name = region.xpath('a/text()')[0]
                if region_name in district:
                    region_href = self._DOMAIN + region.xpath('a/@href')[0] + 'e1/'
                    resp = self.sess.get(region_href, headers=self.headers).text
                    tree = html.fromstring(resp)
                    no_result = tree.xpath('//div[@class="no-list-box w mt10"]')
                    if no_result:
                        msg = no_result[0].xpath('p/text()')[0]
                        return msg
                    else:
                        return_result = []
                        results = tree.xpath('//div[@class="jzList-con w"]/div')
                        for result in results:
                            return_dict = {}
                            return_dict['title'] = result.xpath('div[2]/div/h3/a/text()')[0].strip()

                            return_dict['href'] = self._DOMAIN + result.xpath('div[2]/div/h3/a/@href')[0]
                            return_dict['money'] = result.xpath('div[4]/span[1]/em/text()')[0]
                            return_dict['unit'] = result.xpath('div[4]/span[1]/text()')[0]
                            return_dict['money_type'] = result.xpath('div[4]/span[2]/text()')[0]

                            inform = result.xpath('div[2]/ul')[0]
                            inform_text = etree.tostring(inform, encoding='unicode')
                            return_dict['work_time'] = re.findall('工作时间.*?>(.*?)<', inform_text, re.S)[0].strip()
                            return_dict['work_type'] = inform.xpath('li[2]/text()')[0].strip()
                            return_dict['work_location'] = inform.xpath('li[3]/text()')[0].strip()
                            return_dict['people_nums'] = inform.xpath('li[4]/text()')[0].strip()
                            return_result.append(return_dict)
                        return return_result


        else:
            msg = '未找到该城市兼职'
            return msg

    def get_amap_json(self):
        location = self.location[1] + ',' + self.location[0]
        key = '31e74c190929ba20ddd95ff17f62d28e'
        geo_json = requests.get(
            url='http://restapi.amap.com/v3/geocode/regeo',
            params={
                'key': key,
                'location': location,
            }
        ).json()
        return geo_json

    def get_region(self):
        geo_json = self.get_amap_json()
        addressComponent = geo_json['regeocode']['addressComponent']
        province = addressComponent['province']
        if province.endswith('省'):
            city = addressComponent['city']
        elif province.endswith('市'):
            city = province
        else:
            raise ValueError
        district = addressComponent['district']
        return city, district

    def get_all_citys(self):
        resp = self.sess.get(self._CITY, headers=self.headers).text
        tree = html.fromstring(resp)
        all_city = tree.xpath('//div[@class="all-city"]/dl/dd')
        city_list = []
        city_dict = {}
        for dd in all_city:
            citys = dd.xpath('a')
            for city in citys:
                city_name = city.xpath('text()')[0]
                city_href = city.xpath('@href')[0]
                city_list.append(city_name)
                city_dict[city_name] = city_href
        return city_list, city_dict


if __name__ == '__main__':
    # 121.682691,31.0124169
    location = ('31.0124169', '121.682691')
    x = JianZhi('上海市', '浦东新区')
    print(x.get_jobs())
