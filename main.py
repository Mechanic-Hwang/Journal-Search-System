# journal_search_system/main.py

import os
import shutil
from datetime import datetime
from fastapi import FastAPI, UploadFile, File, Form, Request, Query
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from sqlalchemy import create_engine, Column, Integer, String, Text, Date, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker
from typing import List
import pandas as pd
import re

from starlette.responses import RedirectResponse

from models.models import Base, Journal, UploadLog
from database.database import engine
from translations.dictionary import translations
from utils.i18n import get_locale, get_translator
from utils.util import parse_date, safe_str

Base.metadata.create_all(bind=engine)

app = FastAPI()

# Set up static
# app.mount("/static", StaticFiles(directory="static"), name="static")

# Database setup
DATABASE_URL = "sqlite:///./journal.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()
templates = Jinja2Templates(directory="templates")

@app.get("/", response_class=HTMLResponse)
def search_page(request: Request):
    try:
        lang = request.query_params.get("lang", "zh_mo")
        translation = translations.get(lang, translations["zh_mo"])
        return templates.TemplateResponse("search.html", {
            "request": request,
            "lang": lang,
            "translation": translation,
        })
    except Exception as e:
        print("模板渲染出错：", str(e))
        raise e

# Upload Endpoint
@app.get("/upload", response_class=HTMLResponse)
async def upload_page(request: Request, lang: str = "zh_mo"):
    translation = translations.get(lang, translations["zh_mo"])
    return templates.TemplateResponse("upload.html", {
        "request": request,
        "lang": lang,
        "translation": translation,
        "results": []
    })


@app.post("/upload")
async def upload_excel(request: Request, file: UploadFile = File(...), lang: str = "zh_mo"):
    session = SessionLocal()
    translation = translations.get(lang)
    upload_results = []

    today_str = datetime.now().strftime("%Y_%m_%d")
    save_dir = os.path.join("excel", today_str)
    os.makedirs(save_dir, exist_ok=True)
    file_path = os.path.join(save_dir, file.filename)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    try:
        # 尝试读取所有 Sheet
        xls = pd.ExcelFile(file_path)
        sheet_names = xls.sheet_names
    except Exception:
        return templates.TemplateResponse("upload.html", {
            "request": request,
            "translation": translation,
            "lang": lang,
            "error": translation['file_error']
        })

    required_columns = [
        "ARTICLE_ID", "TITLE", "AUTHOR", "ABSTRACT", "SOURCE_ID", "CUM_ISSUE",
        "SERIES", "VOL_NO", "PAGE_NO", "SEARCH_DATE", "DISPLAY_DATE", "KEYWORD", "Url_link"
    ]

    for sheet in sheet_names:
        try:
            df = xls.parse(sheet)
        except Exception as e:
            upload_results.append({
                "title": f"[{sheet}]",
                "result": translation["fail"],
                "reason": f"{translation['file_error']} ({str(e)})"
            })
            continue

        # 检查字段完整性
        for col in required_columns:
            if col not in df.columns:
                upload_results.append({
                    "title": f"[{sheet}]",
                    "result": translation["fail"],
                    "reason": f"{translation['missing_field']}: {col}"
                })
                break  # 当前 sheet 不继续处理

        for _, row in df.iterrows():
            title = str(row['TITLE']).strip()
            if not title or title.lower() == 'nan':
                result = translation['fail']
                reason = translation['empty_title']
            elif session.query(Journal).filter(Journal.title == title).first():
                result = translation['fail']
                reason = translation['duplicate_title']
            else:
                try:
                    search_date = parse_date(str(row['SEARCH_DATE'])) if not pd.isna(row['SEARCH_DATE']) else None
                    if not search_date:
                        raise ValueError(translation['date_format_error'])
                    journal = Journal(
                        article_id=safe_str(row['ARTICLE_ID']),
                        title=safe_str(row['TITLE']),
                        author=safe_str(row['AUTHOR']),
                        abstract=safe_str(row['ABSTRACT']),
                        source_id=safe_str(row['SOURCE_ID']),
                        cum_issue=safe_str(row['CUM_ISSUE']),
                        series=safe_str(row['SERIES']),
                        vol_no=safe_str(row['VOL_NO']),
                        page_no=safe_str(row['PAGE_NO']),
                        search_date=search_date,
                        display_date=safe_str(row['DISPLAY_DATE']),
                        keyword=safe_str(row['KEYWORD']),
                        url_link=safe_str(row['Url_link'])
                    )
                    session.add(journal)
                    session.commit()
                    result = translation['success']
                    reason = ""
                except Exception as e:
                    result = translation['fail']
                    reason = str(e)

            log = UploadLog(title=title, result=result, reason=reason)
            session.add(log)
            upload_results.append({"title": title, "result": result, "reason": reason})

    session.commit()
    session.close()
    return templates.TemplateResponse("upload.html", {
        "request": request,
        "translation": translation,
        "lang": lang,
        "results": upload_results
    })



@app.get("/manual_upload")
async def manual_upload_form(request: Request, lang: str = "zh_mo"):
    translation = translations.get(lang)
    return templates.TemplateResponse("manual_upload.html", {
        "request": request,
        "translation": translation,
        "lang": lang
    })


@app.post("/manual_submit")
async def manual_submit(
    request: Request,
    article_id: str = Form(""),
    title: str = Form(""),
    author: str = Form(""),
    abstract: str = Form(""),
    source_id: str = Form(""),
    cum_issue: str = Form(""),
    series: str = Form(""),
    vol_no: str = Form(""),
    page_no: str = Form(""),
    search_date: str = Form(""),
    display_date: str = Form(""),
    keyword: str = Form(""),
    url_link: str = Form(""),
    lang: str = Form("zh_mo")
):
    session = SessionLocal()
    error = None

    if not title.strip():
        error = translations.get(lang)['title_required']
    else:
        try:
            journal = Journal(
                article_id=article_id.strip() or None,
                title=title.strip(),
                author=author.strip() or None,
                abstract=abstract.strip() or None,
                source_id=source_id.strip() or None,
                cum_issue=cum_issue.strip() or None,
                series=series.strip() or None,
                vol_no=vol_no.strip() or None,
                page_no=page_no.strip() or None,
                search_date=parse_date(search_date.strip()) if search_date.strip() else None,
                display_date=display_date.strip() or None,
                keyword=keyword.strip() or None,
                url_link=url_link.strip() or None
            )
            session.add(journal)
            session.commit()

            log = UploadLog(title=title.strip(), result="成功", reason="手動上傳")
            session.add(log)
            session.commit()
        except Exception as e:
            error = str(e)

    session.close()

    if error:
        translation = translations.get(lang)
        return templates.TemplateResponse("manual_upload.html", {
            "request": request,
            "translation": translation,
            "error": error,
            "lang": lang
        })
    return RedirectResponse(url=f"/manual_upload?lang={lang}", status_code=302)