# journal_search_system/main.py

import os
import shutil
from datetime import datetime
from fastapi import FastAPI, UploadFile, File, Form, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from sqlalchemy import create_engine, Column, Integer, String, Text, Date, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker
from typing import List
import pandas as pd
import re
from models.models import Base, Journal, UploadLog
from database.database import engine
from utils.i18n import get_locale, get_translator
from utils.util import parse_date

Base.metadata.create_all(bind=engine)

app = FastAPI()

# Set up static
app.mount("/static", StaticFiles(directory="static"), name="static")

# Database setup
DATABASE_URL = "sqlite:///./journal.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()




app = FastAPI()
templates = Jinja2Templates(directory="app/templates")

@app.get("/", response_class=HTMLResponse)
def search_page(request: Request):
    lang = get_locale(request)
    translator = get_translator(lang)
    _ = translator.gettext
    return templates.TemplateResponse("search.html", {
        "request": request,
        "lang": lang,
        "_": _,
    })

# Upload Endpoint
@app.get("/upload", response_class=HTMLResponse)
async def upload_page(request: Request):
    return templates.TemplateResponse("upload.html", {"request": request})

@app.post("/upload")
async def upload_excel(request: Request, file: UploadFile = File(...)):
    session = SessionLocal()
    upload_results = []
    today_str = datetime.now().strftime("%Y_%m_%d")
    save_dir = os.path.join("excel", today_str)
    os.makedirs(save_dir, exist_ok=True)
    file_path = os.path.join(save_dir, file.filename)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    df = pd.read_excel(file_path)
    required_columns = [
        "ARTICLE_ID", "TITLE", "AUTHOR", "ABSTRACT", "SOURCE_ID", "CUM_ISSUE",
        "SERIES", "VOL_NO", "PAGE_NO", "SEARCH_DATE", "DISPLAY_DATE", "KEYWORD", "Url_link"
    ]
    for col in required_columns:
        if col not in df.columns:
            return templates.TemplateResponse("upload.html", {"request": request, "error": f"缺少字段: {col}"})

    for index, row in df.iterrows():
        title = str(row['TITLE']).strip()
        if not title or title == 'nan':
            result = "失败"
            reason = "标题为空"
        elif session.query(Journal).filter(Journal.title == title).first():
            result = "失败"
            reason = "标题重复"
        else:
            try:
                search_date = parse_date(str(row['SEARCH_DATE']))
                if not search_date:
                    raise ValueError("日期格式错误")
                journal = Journal(
                    article_id=str(row['ARTICLE_ID']),
                    title=title,
                    author=str(row['AUTHOR']),
                    abstract=str(row['ABSTRACT']),
                    source_id=str(row['SOURCE_ID']),
                    cum_issue=str(row['CUM_ISSUE']),
                    series=str(row['SERIES']),
                    vol_no=str(row['VOL_NO']),
                    page_no=str(row['PAGE_NO']),
                    search_date=search_date,
                    display_date=str(row['DISPLAY_DATE']),
                    keyword=str(row['KEYWORD']),
                    url_link=str(row['Url_link'])
                )
                session.add(journal)
                session.commit()
                result = "成功"
                reason = ""
            except Exception as e:
                result = "失败"
                reason = str(e)

        log = UploadLog(title=title, result=result, reason=reason)
        session.add(log)
        upload_results.append({"title": title, "result": result, "reason": reason})

    session.commit()
    session.close()
    return templates.TemplateResponse("upload.html", {"request": request, "results": upload_results})
