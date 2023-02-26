from tqdm import tqdm
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
import requests
from bs4 import BeautifulSoup
import json
import pymongo
import argparse

parser = argparse.ArgumentParser()
parser.add_argument(
    '--url', type=str, default='https://documentation.softwareag.com/webmethods/api_gateway/yai10-15/webhelp/yai-webhelp/yai-webhelp.html')
parser.add_argument('--output', type=str, default='data.json')
parser.add_argument('--driver', type=str, default='./chromedriver')


url = parser.parse_args().url
response = requests.request("GET", url, data="")


soup = BeautifulSoup(response.text, 'html.parser')


# write a function to get links in the deepest level of the soup
def get_links(soup):
    links = set()
    if soup.find('li') is None:
        links.add(soup.find('a').get('href'))
    else:
        for li in soup.find_all('li'):
            links = links.union(get_links(li))
    return links


allLinks = get_links(soup)


baseUrl = url.split()


links = [baseUrl + link for link in allLinks]


open('links.txt', 'w').write('\n'.join(links))


driver = webdriver.Chrome(parser.parse_args().driver)


client = pymongo.MongoClient("mongodb://localhost:27017/")
collection = client["documentation"][url.split('-')[-2].split('/')[-1]]


dataDict = {}
exceptionsList = []
for link in tqdm(links):
    try:
        driver.get(link)
        driver.implicitly_wait(30)
        title = driver.title
        driver.switch_to.frame(driver.find_element_by_tag_name("iframe"))
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        soup = soup.find('body')
        soup.header.decompose()
        soup.footer.decompose()
        data = soup.text.strip().replace('\n', ' ')
        temp = {'text': data, 'link': link, 'title': title}
        collection.insert_one(temp)
    except Exception as e:
        print(e)
        exceptionsList.append(link)


json.dump(dataDict, open(parser.parse_args().output, 'w'))
