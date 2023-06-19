import logging

from db.db import SessionLocal
from db.models import Article
from sqlalchemy import desc
from sqlalchemy.orm import Session


logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format=u'[%(asctime)s] - %(message)s')
logger.info("Start service")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


async def db_create_article(art_dict, db: Session):
    db_article = Article(
        name=art_dict['name'],
        description=art_dict['description'],
        image=art_dict['image'],
        origin=art_dict['origin'],
        source=art_dict['source'],
        tags=art_dict['tags'],
        date=art_dict['date'],
        url=art_dict['url'],
        id_from_kycbase=art_dict['id_from_kycbase']
    )
    db.add(db_article)
    db.commit()
    logger.info(f'Article {art_dict["id_from_kycbase"]} is added to db.')
    return db_article.id_from_kycbase


async def db_get_article_by_kycbase_id(id_from_kycbase, db: Session):
    db_article = db.query(Article).filter(Article.id_from_kycbase == id_from_kycbase).first()
    return db_article


async def db_get_last_hundred_of_article_names(db: Session):
    db_article_names = db.query(Article.name).order_by(desc(Article.date_of_loading)).limit(100)
    list_to_return = [i[0] for i in db_article_names]
    return list_to_return


async def db_get_article_collision(name, db: Session):
    db_article_collision = db.query(Article).filter(Article.name == name).first()
    if db_article_collision:
        return True
    else:
        return None


def db_delete_article_by_kycbase_id(id_from_kycbase, db: Session):
    article_to_delete = db.query(Article).filter(Article.id_from_kycbase == id_from_kycbase).first()
    db.delete(article_to_delete)
    db.commit()
    return f'Article "{id_from_kycbase}" deleted.'
