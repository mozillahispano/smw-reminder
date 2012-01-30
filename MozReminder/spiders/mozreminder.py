from scrapy.spider import BaseSpider
from scrapy.selector import HtmlXPathSelector

from MozReminder.items import MozreminderItem

class TareaSpider(BaseSpider):
  name = "tareas"
  allowed_domains = ["mozilla-hispano.org"]
  start_urls = [
	"https://www.mozilla-hispano.org/documentacion/Tareas"
  ]

  def parse(self, response):
      hxs = HtmlXPathSelector(response)
      sites = hxs.select('//table/tr')
      items = []
      for site in sites:
          item = MozreminderItem()
          item['tarea'] = site.select('td/a/text()').extract()
          'link_tarea' = site.select('td/a/@href').extract()
          item['limite'] = site.select('td[6]/text()').extract()
	  items.append(item)
      for url in 'link_tarea':
	  yield Request(url, callback=self.parse_links)
  def parse_links(self, response):
      hxs = HtmlXPathSelector(response)
      links = hxs.select('//div[@id="bodyContent"]/ul/li/a')
      for link in links
	  item['responsable'] = link.select('text()').extract()
	  'link_user' = link.select('@href').extract()
      for url in 'link_user':
	  yield Request(url, callback=self.parse_user)
  def parse_user(self, response):
      hxs = HtmlXPathSelector(response)
      users = hxs.select('//table/tr[10]/td[2]')
      for user in users
	  item['mail'] = user.select('text()').extract()
      return items
