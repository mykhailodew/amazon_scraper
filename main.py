import requests
import re
import locale
import csv
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from os import listdir
from os.path import isfile, join
from datetime import datetime
from lxml import html

csv_file = open('Amazon.csv', 'w', newline='')
writer = csv.writer(csv_file)

start_urls = []

locale.setlocale(locale.LC_ALL, 'fr_FR.UTF-8')
folder_path = 'links/'
link_files = [f for f in listdir(folder_path) if isfile(join(folder_path, f))]

for link_file in link_files:
    buffer = open(folder_path + link_file, 'r')

    for line in buffer.readlines():
        start_urls.append(line.split(';')[1])

    buffer.close()

service = Service(executable_path='chromedriver.exe')
options = Options()
options.headless = True
driver = webdriver.Chrome(service=service, options=options)

headers = {'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/99.0.4844.82 Safari/537.36'}
proxies = {'http': 'http://pxu28414-0:TnTBWRRHOY5G2Rlo4nGg@x.botproxy.net:8080', 'https': 'http://pxu28414-0:TnTBWRRHOY5G2Rlo4nGg@x.botproxy.net:8080'}

for url in start_urls:
    r = requests.get(url, headers=headers, proxies=proxies)
    response = html.fromstring(r.content)

    if r.status_code == 200:
        item = {
            'reference': '',
            'price': 0,
            'prime': True,
            'quantity': 0,
            'shipping': None
        }

        try:
            item['reference'] = re.search(r'dp/(\w+)/', r.url).group(1)
        except:
            item['reference'] = re.search(r'gp/product/(\w+)/', r.url).group(1)
        print(item['reference'])
        box = response.xpath('//div[@class="a-box"]')

        if len(box) == 0:
            box = response.xpath('//div[@class="a-box a-last"]')

        if len(box) == 0:
            box = response.xpath('//div[@id="buybox"]')

        try:
            item['price'] = float(
                re.sub('[\s€]', '', box[0].xpath('.//span[@class="a-offscreen"]/text()')[0]).replace(',', '.'))
        except:
            item['price'] = 0.0
        print(item['price'])
        if item['price'] == 0:
            continue

        try:
            if box[0].xpath('.//div[@class="tabular-buybox-text"]/div/span/text()')[0] == 'Amazon':
                item['prime'] = True
            else:
                item['prime'] = False
        except:
            item['prime'] = False
        print(item['prime'])

        if len(box[0].xpath('.//div[@id="usedBuySection"]')) == 0:
            selector = box[0].xpath('.//select[@name="quantity"]//option')

            if len(selector) == 0:
                availability = box[0].xpath('.//div[@id="availability"]/span/text()')

                if availability is not None:
                    if availability.strip() == 'Il ne reste plus que 1 exemplaire(s) en stock.':
                        item['quantity'] = 1
                    else:
                        item['quantity'] = 0
                else:
                    item['quantity'] = 0
            else:
                item['quantity'] = len(selector)
        else:
            item['quantity'] = 0
        print(item['quantity'])
        delivery_msg = box[0].xpath('.//span[@data-csa-c-type="element"]//@data-csa-c-delivery-time')
        if len(delivery_msg) != 0:
            item['shipping'] = delivery_msg[0]

        if item['shipping'] is None:
            driver.get(r.url)

            try:
                delivery_msg = driver.find_element(By.XPATH, '//span[@data-csa-c-type="element"]')
                item['shipping'] = delivery_msg.get_attribute('data-csa-c-delivery-time')
            except:
                pass
        print(item['shipping'])
        if item['shipping'] is None:
            continue

        delivery_date_str = re.match(r'\w+\s\d+\s\w+', item['shipping'])
        delivery_date = None

        if delivery_date_str is None:
            delivery_date_str = re.match(r'(\d+\s\w+)\s-\s\d+\s\w+', item['shipping'])

            if delivery_date_str is None:
                delivery_date_str = re.match(r'(\d+)\s-\s\d+\s(\w+)', item['shipping'])

                if delivery_date_str is not None:
                    delivery_date = datetime.strptime(delivery_date_str.group(1) + ' ' + delivery_date_str.group(2),
                                                      '%d %B')
                    delivery_date = datetime(datetime.today().year, delivery_date.month, delivery_date.day)
            else:
                delivery_date = datetime.strptime(delivery_date_str.group(1), '%d %B')
                delivery_date = datetime(datetime.today().year, delivery_date.month, delivery_date.day)
        else:
            delivery_date = datetime.strptime(item['shipping'], '%A %d %B')
            delivery_date = datetime(datetime.today().year, delivery_date.month, delivery_date.day)

        delta = delivery_date - datetime.today()

        if delta.days > 7:
            continue

        print(item)
        writer.writerow(item.values())

driver.quit()
csv_file.close()
