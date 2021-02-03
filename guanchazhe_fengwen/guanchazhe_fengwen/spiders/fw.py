import scrapy
from parsel import Selector


class FwSpider(scrapy.Spider):
    name = 'fw'
    # allowed_domains = ['fw.com']
    start_url = 'https://user.guancha.cn/main/index-list.json?page={}&order=1'

    def start_requests(self):
        for i in range(1, 101):
            yield scrapy.Request(url=self.start_url.format(i), callback=self.parse)

    def parse(self, response):
        links = response.xpath('//div[@class="list-item"]/h4/a/@href').getall()
        for link in links:
            yield response.follow(url=link, callback=self.parse_detail)

    def parse_detail(self, response):
        title = response.xpath('//div[@class="article-content"]/h1/text()').get()

        author = response.xpath('//div[@class="user-main"]/h4/a/text()').get()
        contents = response.xpath('//div[@class="article-txt-content"]//p/text()').getall()
        content = '_'.join(x.strip() for x in contents)
        release_time = response.xpath('//div[@class="user-main"]/p/span[@class="time1"]/text()').get()
        imgs = response.xpath('//div[@class="article-txt-content"]//p//img/@src').getall()

        item = {}
        item['title'] = title
        item['author'] = author
        item['content'] = content
        item['release_time'] = release_time
        item['imgs'] = imgs
        yield item

        load_art_more = 'https://user.guancha.cn/user/personal-homepage'
        uid = response.xpath('//div[@class="user-avatar popup-user"]/@user-id').get()
        page = 1
        meta = response.meta
        try:
            page = meta['page']
        except:
            meta['page'] = 1
        meta['uid'] = uid

        data = {
            'page': str(page),
            'addMore': 'published',
            'uid': uid
        }
        # print(data)
        yield scrapy.FormRequest(url=load_art_more, formdata=data, meta=meta, callback=self.parse_author)

    def parse_author(self, response):
        print(' into parse_author func ')
        # print('response.text :', response.text)
        meta = response.meta
        meta['page'] +=1
        if len(response.text) < 50:
            print('response.text :', response.text)
            return
        # print('start next page request ')
        load_art_more = 'https://user.guancha.cn/user/personal-homepage'
        data = {
            'page': str(meta['page']),
            'addMore': 'published',
            'uid': str(meta['uid'])
        }
        yield scrapy.FormRequest(url=load_art_more, formdata=data, meta=meta)
        # print('parse_author, start formrequest')
        rsp = Selector(response.text.replace('\\"', '"'))
        links = rsp.xpath('//div[@class="normal"]/h4/a/@href').getall()
        # print(links)
        for link in links:
            yield response.follow(url=link, callback=self.parse_detail, meta=meta)
