import base64
import json
import os
import random
import aiohttp
import time
import datetime
import logging
import re
import asyncio

from html import escape
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from db.db_functions import db_create_article, get_db
from sqlalchemy.orm import Session
from fastapi import Depends
from config import url_to_download, headers
# from test_request import test_article_NO_image, test_article_WITH_image


logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format=u'[%(asctime)s] - %(message)s')
logger.info("Start service")


async def get_dates_list(year: int, month: int, day: int) -> list:
    start_date = datetime.date(year, month, day)
    end_date = datetime.date.today()
    dates_list = []
    while start_date < end_date:
        dates_list.append(start_date.strftime('%Y-%m-%d'))
        if start_date.month == 12:
            start_date = start_date.replace(year=start_date.year+1, month=1)
        else:
            start_date = start_date.replace(month=start_date.month+1)
    logger.info("Dates_list returned")
    return dates_list


async def get_html(start_date):
    if not os.path.exists("links/base_htmls"):
        os.mkdir("links/base_htmls")

    driver = webdriver.Chrome()
    driver.maximize_window()

    try:
        driver.get(url=f"https://www.kommersant.ru/archive/news/month/{start_date}")
        while True:
            next_element_button = driver.find_element(By.CSS_SELECTOR, "button.doc_button--rubric")
            element_under_button = driver.find_element(By.CLASS_NAME, "ba__tag--black")
            logger.info("Button is found")
            try:
                if driver.find_element(By.CSS_SELECTOR, "div.js-archive-more.hide"):
                    with open(f"links/base_htmls/{start_date}.html", "w") as file:
                        file.write(driver.page_source)
                        logger.info(f"{start_date}.html completed")
                        break
            except:
                if next_element_button:
                    try:
                        driver.execute_script("arguments[0].scrollIntoView();", element_under_button)
                        time.sleep(2)
                        next_element_button.click()
                        time.sleep(2)
                        logger.info("Next scrolling")
                    except Exception as ex:
                        logger.info(f"SCROLLING EXCEPTION {ex}")
                        continue

    except Exception as ex:
        logger.info(f"Get_html EXCEPTION: {ex}")

    finally:
        driver.close()
        driver.quit()


async def get_links(html_file, file_date):
    if not os.path.exists("links/links_files"):
        os.mkdir("links/links_files")

    with open(html_file) as file:
        src = file.read()

    soup = BeautifulSoup(src, "lxml")
    articles = soup.find_all("article")

    list_to_append = []

    for i in articles:
        link = i.get('data-article-url')
        if link:
            date = i.find('p', class_='rubric_lenta__item_tag')
            if date:
                date = date.text.split(',')[0]
            tags_blocks = i.find_all('a', class_='tag_list__link')
            if tags_blocks:
                tags = [i.text for i in tags_blocks]
            else:
                tags = None
            url_part = i.find('a', class_='uho__link')
            if url_part:
                url_part = url_part['href']
            list_to_append.append(
                {
                    'link': link,
                    'date': date.split()[0],
                    'tags': tags,
                    'url_part': url_part
                }
            )

    with open(f'links/links_files/{file_date}.json', 'w') as f:
        json.dump(list_to_append, f, indent=4, ensure_ascii=False)
        logger.info(f'Json file {file_date}.json has been created.')

            # print(link, '\n', date, '\n', tags, '\n')
    #         if link:
    #             f.write(link + '\n')
    # logger.info(f"File {file_date}.txt is finished")


async def get_page_data(file_date, source, date, tags, url_part):
    async with aiohttp.ClientSession() as session:
        counter = 0
        while True:
            async with session.get(source) as response:
                if response.status == 200:
                    text_html = await response.text()
                    break
                else:
                    delay = random.randint(1, 5)
                    await asyncio.sleep(delay)
                    counter += 1
                    if counter == 7:
                        delay2 = random.randint(7, 20)
                        await asyncio.sleep(delay2)
                        counter = 0

    soup = BeautifulSoup(text_html, "lxml")

    allowed_tags = ['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'em', 'b', 'i', 'a', 'img', 'p']
    allowed_attributes = ['href', 'src']

    article_block = soup.find("div", class_="lenta_top_doc")
    # article_body = article_block.find("div", class_="doc__body")
    article_body = article_block.find("div", class_="article_text_wrapper")
    new_soup = BeautifulSoup(parser="lxml")
    article_name = article_block.find('h1', class_="doc_header__name")
    new_soup.append(article_name)
    name = article_name.text.strip()

    for tag in article_body.findAll(True):
        if tag.name in allowed_tags:
            new_soup.append(tag)

    image_list = new_soup.find_all('img')
    if image_list:
        image = image_list[1]['src']
    else:
        image = None

    for tag in new_soup:
        if tag.findAll(True):
            for inside_tag in tag.findAll(True):
                if inside_tag.name not in allowed_tags:
                    inside_tag.decompose()
                else:
                    new_text = inside_tag.string
                    if new_text:
                        inside_tag.string = escape(new_text)
                    else:
                        if inside_tag.findAll(True):
                            for inside_inside_tag in inside_tag.findAll(True):
                                if inside_inside_tag.name not in allowed_tags:
                                    inside_inside_tag.decompose()
                                else:
                                    new_new_text = inside_inside_tag.string
                                    if new_new_text:
                                        inside_inside_tag.string = escape(new_new_text)

        else:
            new_text = tag.string
            if new_text:
                tag.string = escape(new_text)

        attrs = list(tag.attrs.keys())

        for attr in attrs:
            if attr not in allowed_attributes:
                del tag.attrs[attr]

        if tag.name == 'a':
            if re.match(r"^/doc/", tag.get("href")) or re.match(r"^/gallery/", tag.get("href")):
                tag["href"] = 'https://www.kommersant.ru' + tag.get("href")

        if tag.name == 'img':
            if re.match(r"^https", tag.get('src')):
                photo_url = f'{tag.get("src")}'
                async with aiohttp.ClientSession() as session:
                    async with session.get(photo_url) as response:
                        image_bytes = await response.content.read()
                    encoded_image = base64.b64encode(image_bytes)
                    result = encoded_image.decode('utf-8')

                    # print(result)
                    # with open("image_test.jpg", "wb") as f:
                    #     f.write(base64.b64decode(result))

                    tag["src"] = f"data:image/jpg;base64,{result}"
    new_soup = re.sub(r'(\n)', r'<br>', str(new_soup), flags=re.DOTALL)
    description = str(new_soup)
    image = image
    origin = 'https://www.kommersant.ru/'
    source = source
    tags = tags
    date = date
    url = url_part
    logger.info(f"Article: {name} has been scrapped.")
    # print(json.loads(json.dumps(description)))
    # print(description)
    return {
        'name': name,
        'description': description,
        'image': image,
        'origin': origin,
        'source': source,
        'tags': tags,
        'date': date,
        'url': url
    }


async def make_final_json(file_date):
    with open(f'links/links_files/{file_date}.json') as file:
        data = json.load(file)

    final_list = []
    counter = 0
    for dat in data:
        final_dict = await get_page_data(
            file_date=file_date,
            source=dat.get('link'),
            date=dat.get('date'),
            tags=dat.get('tags'),
            url_part=dat.get('url_part'))
        final_list.append(final_dict)
        counter += 1
        logger.info(f'{counter}')

    if not os.path.exists("final_jsons"):
        os.mkdir("final_jsons")

    with open(f'final_jsons/final_{file_date}.json', 'w') as f:
        json.dump(final_list, f, indent=4, ensure_ascii=False)
        logger.info(f'Json final file {file_date}.json has been created.')


async def send_to_site(file_date, db):
    with open(f'final_jsons/final_{file_date}.json') as f:
        data = json.load(f)

    for dat in data:
        # async with aiohttp.ClientSession() as session:
        #     async with session.post(url_to_download, json=json.dumps(dat)) as response:
        #         if response.status == 200:
        #             result = await response.json()
        result = {'id': 1111}
        dat['id_from_kycbase'] = result['id']
        await db_create_article(art_dict=dat, db=db)


    # arti_no_im = test_article_NO_image
    # arti_with_im = test_article_WITH_image
    # async with aiohttp.ClientSession() as session:
    #     async with session.post(url_to_download, json=json.dumps(arti_no_im)) as response:
    #         if response.status == 200:
    #             result = await response.json()
    #             print(result)
    #             arti_no_im['id_from_kycbase'] = result['id']
    #             await db_create_article(art_dict=arti_no_im, db=db)
    #         else:
    #             print(response.status)


    # async with aiohttp.ClientSession() as session:
    #     async with session.post(url_to_download, json=json.dumps(arti_with_im)) as response:
    #         if response.status == 200:
    #             result = await response.json()
    # arti_no_im['id_from_kycbase'] = result['id']
    # await db_create_article(art_dict=arti_no_im, db=db)



async def main(year, month, day, db: Session = Depends(get_db)):
    dates_list = await get_dates_list(year=year, month=month, day=day)
    for i in dates_list[:2-1]:
        try:
            # await get_html(start_date=i)
            # await get_links(html_file=f"links/base_htmls/{i}.html", file_date=i)
            # await make_final_json(file_date=i)
            await send_to_site(file_date=i, db=db)
        except Exception as ex:
            logger.info(f'Main EXCEPTION: {ex}')


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main(year=2022, month=6, day=1))
