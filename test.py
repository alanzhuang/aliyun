import requests
from lxml import html
import warnings
import pymysql
import time
import hashlib

warnings.filterwarnings("ignore")


def runc(info, db, r, pp):
    url = info['url']
    keyword = info['keyword']
    title = info['title']
    publish_time = info['publish_time']
    try:
        resp, pp = get_resp(url, r, pp)
    except:
        print('获取文章详情失败' + url)
        r.sadd("tandfon_url", info)

    else:
        if resp:
            get_detail(resp, db, title, keyword, publish_time, url)


def get_detail(resp, db, title, keyword, publish_time, url):
    tree = html.fromstring(resp)
    authors_info = tree.xpath('//span[@class="NLM_contrib-group"]')
    if authors_info:
        authors = authors_info[0]
        authorsWithEmail = authors.xpath('span[contains(@class,"corresponding")]')
        for author in authorsWithEmail:
            name = author.xpath('a[@class="entryAuthor"]/text()')[0]
            email = author.xpath('a[@class="entryAuthor"]/span/span/span[@class="corr-email"]/text()')[0]
            raw = name + email + title + keyword + publish_time
            rawdata = hashlib.md5(raw.encode('utf-8')).hexdigest()
            cursor = db.cursor()
            sql = "INSERT INTO zhuang(title,keyword,publication_time,author,email,rawdata,url)VALUES ('%s','%s','%s', '%s', '%s', '%s', '%s')" % (
                pymysql.escape_string(title), keyword, publish_time.strip(), name, email, rawdata, url)
            print(sql)
            try:
                cursor.execute(sql)
            except Exception as e:
                pass
            else:
                db.commit()


def get_resp(url, r, pp):
    headers = {
        'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 11_0 like Mac OS X) AppleWebKit/604.1.38 (KHTML, like Gecko) Version/11.0 Mobile/15A372 Safari/604.1'
    }
    i = 0
    while i < 4:
        try:
            print('使用代理：' + str(pp))
            resp = requests.get(url, headers=headers, verify=False, timeout=5, proxies=eval(pp)).text
        except Exception as e:
            i += 1
            r.srem('proxy_list', pp)
            print('发生错误' + str(e))
            print('删除代理:' + str(pp))
            pp = get_proxy(r)
            import traceback
            print('第' + str(i) + '次部署')
        else:
            break
    if i == 4:
        raise Exception
    return resp, pp


def get_proxy(r):
    pp = r.srandmember('proxy_list')
    while not pp:
        time.sleep(10)
        return get_proxy(r)
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
    db = pymysql.connect(host="sh-cdb-gsw750ll.sql.tencentcdb.com", port=63599, user="root", password="", db="TESTDB", charset='utf8')
    pp = get_proxy(r)
    while True:
        info_dict = r.spop('tandfon_url')
        if info_dict:
            info = eval(info_dict)
            try:
                runc(info, db, r, pp)
            except Exception:
                r.sadd('tandfon_url', info_dict)
        else:
            print('全部完成')
            break


main()