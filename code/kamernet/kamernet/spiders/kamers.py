# -*- coding: utf-8 -*-
import scrapy
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule


class KamersSpider(CrawlSpider):
    name = 'kamers'
    allowed_domains = ['kamernet.nl']
    # start_urls = ['https://kamernet.nl/huren/kamers-nederland']
    pages_range = range(1, 200, 1)
    start_urls = []
     
    for i in pages_range:
        start_urls.append('https://kamernet.nl/huren/kamers-nederland?pageno=' + str(i))
     
    print(start_urls)
    rules = (
        Rule(LinkExtractor(restrict_xpaths="//div[@id='SearchResultsWrapper']//div[@class='tile-data']/a"), callback='parse_item', follow=True),
        # Rule(LinkExtractor(restrict_xpaths="//div[@class='tile-data']/a"), callback='parse_item', follow=True),
    )

    def parse_item(self, response):
        filename = response.url.split("/")[-1] + '.html'
        with open(filename, 'wb') as f:
            f.write(response.body)
        yield {
            'html': filename,
            'straat': response.xpath("//div[@class='h1_line2 truncate']/text()").get(),
            'plaats': response.xpath("//div[@class='h1_line3']/text()").get(),
            # 'oppervlakte_kamer': response.xpath("normalize-space(/html/body/main/div[1]/div[8]/div[5]/div[1]/div[1]/div[3]/div[1]/div[1]/text())").get(),
            'oppervlakte_kamer': response.xpath("normalize-space(//div[@class='surface']/text())").get(),
            # 'oppervlakte_totaal': response.xpath("//div[@class=total-surface']/text()").get(),
            'oppervlakte_subtitel': ' '.join(x.strip() for x in response.xpath("//div[@class='surface']/following-sibling::*[1]//text()").getall()),
            'prijs': response.xpath("normalize-space(//div[@class='price']/text())").get(),
            'gas_water_licht': response.xpath("//div[@class='gwe']/text()").get(),
            'opleverniveau': response.xpath("normalize-space(//div[@class='furnishing']/text())").get(),
            'beschikbaarheid': response.xpath("normalize-space(//div[@class='availability']/text())").get(),
            'publicatiedatum': response.xpath("//div[@class='published-date']/text()").get(),
            'kamers_url': response.url,
            'woningdetails': dict(response.xpath("//div[text()='Woningdetails']/following-sibling::*/*[2]//*/text()").getall()[i:i+2] for i in range(0, len(response.xpath("//div[text()='Woningdetails']/following-sibling::*/*[2]//*/text()").getall()), 2)),
            # 'html': str(response.body)
            }
                    # 'oppervlakte_totaal': response.xpath("//div[@class=total-surface']/text()").get(),
      

        # item = {}
        # #item['domain_id'] = response.xpath('//input[@id="sid"]/@value').get()
        # #item['name'] = response.xpath('//div[@id="name"]').get()
        # #item['description'] = response.xpath('//div[@id="description"]').get()
        # return item
