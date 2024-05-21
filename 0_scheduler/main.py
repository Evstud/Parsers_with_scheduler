import asyncio
import aiohttp
import aiopg

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from sqlalchemy import create_engine
from fastapi import FastAPI
from pydantic import BaseModel, validator
from datetime import datetime


SCRAPPER_URL = 'http://kommersant:8001/kommersant/'

POSTGRES_USER = "postgres"
POSTGRES_PASSWORD = "password"
POSTGRES_HOSTNAME = "postgres_scheduler"
DATABASE_PORT = 5432
POSTGRES_DB = "db_scheduler"

URL = f'postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOSTNAME}:{DATABASE_PORT}/{POSTGRES_DB}'

app = FastAPI(title="Scheduler")

engine = create_engine(URL)

scheduler = AsyncIOScheduler(timezone="Europe/Moscow")
scheduler.add_jobstore('sqlalchemy', engine=engine)
jobstore = SQLAlchemyJobStore(engine=engine)


class Base(BaseModel):
    scrapper_name: str


class BaseAction(Base):
    action: str

    @validator('action')
    def validate_action(cls, value):
        allowed_values = ['turn_on', 'turn_off']
        if value not in allowed_values:
            raise ValueError(f'action must be one of:{"".join(allowed_values)}')
        return value


@app.on_event("startup")
async def startup_event():
    scheduler.start()


@app.on_event("shutdown")
async def shutdown_event():
    scheduler.shutdown()


@app.post("/scheduler/action/")
async def turn_on_off(model: BaseAction):
    if model.action == "turn_on":
        result = await create_scrapper(name=model.scrapper_name)
        # return result

    elif model.action == "turn_off":
        result = await delete_scrapper(name=model.scrapper_name)
        return result
    else:
        return "Unknown action."


@app.post("/scheduler/add/")
async def create_new_scrapper(model: Base):
    result = await create_scrapper(name=model.scrapper_name)
    # print(result)
    # return print(result)
    return result


async def create_scrapper(name):
    try:
        date = datetime.now()
        job = scheduler.add_job(
            send_request,
            'cron',
            id=name,
            start_date=date,
            minute='*/3'
        )
        if job:
            return job.name
    except Exception as ex:
        return(f"Error: {ex}")


async def send_request():
    async with aiohttp.ClientSession() as session:
        async with session.get(SCRAPPER_URL) as response:
            result = await response.text()
            print(result)


async def delete_scrapper(name):
    try:
        scheduler.remove_job(job_id=name)
        return(f"Job has been deleted.")
    except Exception as ex:
        return(f"Job doesn't deleted: {ex}.")
