import base64
import random
import aiohttp
import logging
import re
import asyncio

from html import escape
from bs4 import BeautifulSoup
from db.db_functions import db_get_last_hundred_of_article_names, db_create_article, get_db, db_get_article_collision
from config import url_to_scrap, url_to_download, headers
from sqlalchemy.orm import Session


logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format=u'[%(asctime)s] - %(message)s')
logger.info("Start service")


async def get_main_html(source):
    logger.info("Get_main_html started.")
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
    logger.info("Get_main_html returned value.")
    return text_html


async def get_links(page_html):
    soup = BeautifulSoup(page_html, "lxml")

    articles = soup.find_all("article", class_="rubric_lenta__item")
    list_to_append = []

    for i in articles:
        link = i.get('data-article-url')
        if link:
            date = i.find('p', class_='rubric_lenta__item_tag')
            if date:
                date = date.text.split('.')[0]
            tags_blocks = i.find_all('a', class_='tag_list__link')
            if tags_blocks:
                tags = [i.text for i in tags_blocks]
            else:
                tags = None
            url_part_block = i.find('a', class_='uho__link')
            if url_part_block:
                url_part = url_part_block['href']
                article_name = url_part_block.string
            else:
                url_part = None
                article_name = None
            list_to_append.append(
                {
                    'link': link,
                    'date': date.split()[0],
                    'tags': tags,
                    'url_part': url_part,
                    'article_name': article_name
                }
            )
    logger.info('Articles list created.')
    return list_to_append


async def verify_new_news(articles_list, db: Session):
    new_articles = []
    for article in articles_list:
        result = await db_get_article_collision(name=article['article_name'], db=db)
        if not result:
            new_articles.append(article)
    if new_articles:
        logger.info('New articles list created.')
    else:
        logger.info('No new articles.')
    return new_articles


async def get_page_data(article):
    async with aiohttp.ClientSession() as session:
        counter = 0
        while True:
            async with session.get(article['link']) as response:
                if response.status == 200:
                    article_text_html = await response.text()
                    break
                else:
                    delay = random.randint(1, 5)
                    await asyncio.sleep(delay)
                    counter += 1
                    if counter == 7:
                        delay2 = random.randint(7, 20)
                        await asyncio.sleep(delay2)
                        counter = 0

    soup = BeautifulSoup(article_text_html, "lxml")

    allowed_tags = ['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'em', 'b', 'i', 'a', 'img', 'p']
    allowed_attributes = ['href', 'src']
    # article_block = soup.find("div", class_="lenta_top_doc")
    article_body = soup.find("div", class_="doc__body")
    # article_body = article_block.find("div", class_="article_text_wrapper")
    new_soup = BeautifulSoup(parser="lxml")
    name = article['article_name']

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
    source = article['link']
    tags = article['tags']
    date = article['date']
    url = article['url_part']
    logger.info(f"Article: {name} has been scrapped.")
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


async def send_and_save(data, db: Session):
    # async with aiohttp.ClientSession() as session:
    #     async with session.post(url_to_download, json=json.dumps(dat)) as response:
    #         if response.status == 200:
    #             result = await response.json()
    result = {'id': 1111}
    data['id_from_kycbase'] = result['id']
    name = data['name']
    result = await db_create_article(art_dict=data, db=db)
    # logger.info(f'Article "{name}" saved to db.')
    return result


async def main(source, db: Session):
    main_page = await get_main_html(source=source)
    links = await get_links(page_html=main_page)
    new_articles_links = await verify_new_news(articles_list=links, db=db)
    if new_articles_links:
        try:
            list_ids_to_return = []
            for article in new_articles_links:
                data_to_save = await get_page_data(article=article)
                result = await send_and_save(data=data_to_save, db=db)
                list_ids_to_return.append(result)
            return f"New articles are added: {list_ids_to_return}"
        except Exception as ex:
            return f"Error: {ex}"
    else:
        return "No new articles."


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main(source=url_to_scrap))
