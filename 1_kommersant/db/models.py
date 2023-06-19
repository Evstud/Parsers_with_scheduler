import datetime
import uuid

from sqlalchemy import Column, Table, String, Integer, ARRAY, DateTime
from sqlalchemy.dialects.postgresql import UUID, DATE
from db.db import Base, engine


class Article(Base):
    __tablename__ = 'article'
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String)
    description = Column(String)
    image = Column(String)
    origin = Column(String)
    source = Column(String)
    tags = Column(ARRAY(String))
    date = Column(String)
    url = Column(String)
    id_from_kycbase = Column(Integer)
    date_of_loading = Column(DateTime, default=datetime.datetime.now)


Base.metadata.create_all(bind=engine)
