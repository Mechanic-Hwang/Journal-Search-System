from sqlalchemy import Column, Integer, String, Date, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class Journal(Base):
    __tablename__ = "journals"

    id = Column(Integer, primary_key=True, index=True)
    article_id = Column(String)
    title = Column(String, nullable=False)
    author = Column(String)
    abstract = Column(Text)
    source_id = Column(String)
    cum_issue = Column(String)
    series = Column(String)
    vol_no = Column(String)
    page_no = Column(String)
    search_date = Column(Date)
    display_date = Column(String)
    keyword = Column(String)
    url_link = Column(String)

    # 备用字段，供后续扩展使用
    extra_field1 = Column(String, nullable=True)
    extra_field2 = Column(String, nullable=True)
    extra_field3 = Column(String, nullable=True)
    extra_field4 = Column(String, nullable=True)
    extra_field5 = Column(String, nullable=True)
    extra_field6 = Column(String, nullable=True)
    extra_field7 = Column(String, nullable=True)
    extra_field8 = Column(String, nullable=True)
    extra_field9 = Column(String, nullable=True)
    extra_field10 = Column(String, nullable=True)


class UploadLog(Base):
    __tablename__ = "upload_logs"

    id = Column(Integer, primary_key=True, index=True)
    upload_time = Column(DateTime, default=datetime.utcnow)
    title = Column(String)
    result = Column(String)
    reason = Column(String)
