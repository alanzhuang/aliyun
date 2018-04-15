import requests
from lxml import html
import warnings
import pymysql
import time

warnings.filterwarnings("ignore")


def runc(info, db, r, pp):
    url = info['url']
    keyword = info['keyword']
    if 'title' not in info.keys():
        try:
            resp,pp = get_resp(url, r, pp)
        except:
            print('获取文章列表失败'+url)
            # r.sadd("tandfon_list",info)
            pass
        else:
            if resp:
                tree = html.fromstring(resp)
                results = tree.xpath('//form[@id="frmSearchResults"]/ol[@class="search-results"]/li')
                for result in results:
                    title = result.xpath('article/@data-title')[0]
                    publish_time = result.xpath('article/div[@class="searchentryright"]/div[last()]/span/text()')[0]
                    href = result.xpath('article/div[1]/span[1]/a[@class="ref nowrap"]/@href')[0]
                    url = 'https://www.tandfonline.com' + href
                    try:
                        resp,pp = get_resp(url, r, pp)
                    except:
                        info['url'] = url
                        info['title'] = title
                        info['publish_time'] = publish_time

                        print('获取文章详情失败' + url)
                        # r.sadd("tandfon_list",info)
                        pass
                    else:
                        if resp:
                            get_detail(resp, db, title, keyword, publish_time)
    else:
        title = info['title']
        publish_time = info['publish_time']
        try:
            resp, pp = get_resp(url, r, pp)
        except:
            print('获取文章详情失败' + url)
            # r.sadd("tandfon_list",info)
            pass
        else:
            if resp:
                get_detail(resp, db, title, keyword, publish_time)

def get_detail(resp,db,title,keyword,publish_time):
    tree = html.fromstring(resp)
    authors_info = tree.xpath('//span[@class="NLM_contrib-group"]')
    if authors_info:
        authors = authors_info[0]
        authorsWithEmail = authors.xpath('span[contains(@class,"corresponding")]')
        for author in authorsWithEmail:
            name = author.xpath('a[@class="entryAuthor"]/text()')[0]
            email = author.xpath('a[@class="entryAuthor"]/span/span/span[@class="corr-email"]/text()')[0]
            cursor = db.cursor()
            sql = "INSERT INTO zhuang(title,keyword,publication_time,author,email)VALUES ('%s','%s', '%s', '%s', '%s')" % (
                pymysql.escape_string(title), keyword, publish_time.strip(), name, email)
            print(sql)
            cursor.execute(sql)
            db.commit()


def get_resp(url, r, pp):
    headers = {
        'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 11_0 like Mac OS X) AppleWebKit/604.1.38 (KHTML, like Gecko) Version/11.0 Mobile/15A372 Safari/604.1'
    }
    i = 0
    while i < 4:
        try:
            print('使用代理：' + str(pp))
            resp = requests.get(url, headers=headers, verify=False, timeout=20, proxies=eval(pp)).text
        except Exception as e:
            i += 1
            r.srem('proxy_list', pp)
            print('发生错误'+str(e))
            print('删除代理:'+str(pp))
            pp = get_proxy(r)
            import traceback
            print('第' + str(i) + '次部署')
        else:
            break
    if i == 4:
        raise Exception
    return resp,pp


def get_proxy(r):
    pp = r.srandmember('proxy_list')
    while not pp:
        resp = requests.get(
            'http://api.xdaili.cn/xdaili-api//privateProxy/applyStaticProxy?spiderId=287e0dc52d2c4e6cb878a29044be25f6&returnType=2&count=1')
        """
        {
        "ERRORCODE":"0",
        "RESULT":[
        {"port":"43617","ip":"222.85.5.118"},
        {"port":"43569","ip":"180.122.20.108"},
        {"port":"20443","ip":"221.230.254.73"}
        ]}
        """
        pp_dict = resp.json()
        if pp_dict['ERRORCODE'] == '0':
            for info in pp_dict['RESULT']:
                print('得到代理：' + str(info))
                # {‘http':'117.25.189.249:28492',‘https':'117.25.189.249:28492'}
                x = {}
                x['http'] = info['ip'] + ':' + info['port']
                x['https'] = info['ip'] + ':' + info['port']
                r.sadd("proxy_list", x)
        else:
            print(pp_dict['ERRORCODE'])
            time.sleep(10)

        pp = r.srandmember('proxy_list')
    return pp


def main():
    import redis, os
    redis_host = os.getenv('redis_host', '118.25.19.129')
    redis_port = os.getenv('redis_port', '6379')
    redis_password = os.getenv('redis_password', '')
    r = redis.Redis(
        host=redis_host,
        port=int(redis_port),
        password=redis_password,
        decode_responses=True
    )
    r.delete('proxy_list')
    db = pymysql.connect("101.132.178.20", "root", "123456", "TESTDB", charset='utf8')
    pp = get_proxy(r)
    while True:
        info_dict = r.spop('tandfon_list')
        if info_dict:
            info = eval(info_dict)
            runc(info, db, r, pp)
        else:
            print('全部完成')
            break


main()
