import requests
from lxml import html
import warnings
import pymysql

warnings.filterwarnings("ignore")


def runc(url, keyword, db):
    resp = get_resp(url)
    if resp:
        tree = html.fromstring(resp)
        results = tree.xpath('//form[@id="frmSearchResults"]/ol[@class="search-results"]/li')
        for result in results:
            title = result.xpath('article/@data-title')[0]
            publish_time = result.xpath('article/div[@class="searchentryright"]/div[last()]/span/text()')[0]
            href = result.xpath('article/div[1]/span[1]/a[@class="ref nowrap"]/@href')[0]
            url = 'https://www.tandfonline.com' + href
            resp = get_resp(url)
            if resp:
                tree = html.fromstring(resp)
                authors_info = tree.xpath('//span[@class="NLM_contrib-group"]')
                if authors_info:

                    authors = authors_info[0]
                    authorsWithEmail = authors.xpath('span[contains(@class,"corresponding")]')
                    for author in authorsWithEmail:
                        name = author.xpath('a[@class="entryAuthor"]/text()')[0]
                        email = author.xpath('a[@class="entryAuthor"]/span/span/span[@class="corr-email"]/text()')[0]
                        cursor = db.cursor()
                        sql = "INSERT INTO zhuang(title,keyword,author,email)VALUES ('%s', '%s', '%s', '%s')" % (
                        pymysql.escape_string(title), keyword, name, email)
                        cursor.execute(sql)
                        db.commit()


def get_resp(url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 11_0 like Mac OS X) AppleWebKit/604.1.38 (KHTML, like Gecko) Version/11.0 Mobile/15A372 Safari/604.1'
    }
    i = 0
    while i < 4:
        try:
            resp = requests.get(url, headers=headers, verify=False, timeout=40).text
        except:
            i += 1
        else:
            break
    if i == 4:
        print(url + '  失败')
        return None

    return resp


def main():
    import redis, os
    redis_host = os.getenv('redis_host', '118.25.19.129')
    redis_port = os.getenv('redis_port', '6379')
    redis_password = os.getenv('redis_password', '54panjiajia')
    r = redis.Redis(
        host=redis_host,
        port=int(redis_port),
        password=redis_password,
        decode_responses=True
    )

    from datetime import datetime
    db = pymysql.connect("localhost", "root", "muou131", "cashbus", charset='utf8')
    print(datetime.now())

    for i in range(0, 50):
        info = eval(r.srandmember('tandfon_list'))
        url = info['url']
        keyword = info['keyword']
        runc(url,keyword,db)
    print(datetime.now())


if __name__ == "__main__":
    main()
