import logging

from fastapi import FastAPI, Depends
from db.db_functions import get_db
from sqlalchemy.orm import Session
import main_kommersant


app = FastAPI(title='Kommersant_scrapper')

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format=u'[%(asctime)s] - %(message)s')
logger.info("Start scrapper")


@app.get('/kommersant/', tags=['Start command'])
async def main_endpoint(db: Session = Depends(get_db)):
    """Endpoint to receive start command."""
    return await main_kommersant.main(
        db=db,
        source=main_kommersant.url_to_scrap
    )
