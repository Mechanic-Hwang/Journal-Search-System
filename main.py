# journal_search_system/main.py

import os
import shutil
from datetime import datetime
from fastapi import FastAPI, UploadFile, File, Form, Request, Query, Depends, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from sqlalchemy import create_engine, Column, Integer, String, Text, Date, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from typing import List, Optional
import pandas as pd
import re

from starlette import status
from starlette.responses import RedirectResponse

from models.models import Base, Journal, UploadLog
from database.database import engine, get_db
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


@app.get("/search_results", response_class=HTMLResponse)
async def search_results(
        request: Request,
        lang: str = "zh_mo",
        query: str = Query(None),
        article_id: str = Query(None),
        title: str = Query(None),
        author: str = Query(None),
        abstract: str = Query(None),
        source_id: str = Query(None),
        cum_issue: str = Query(None),
        series: str = Query(None),
        vol_no: str = Query(None),
        page_no: str = Query(None),
        search_date: str = Query(None),
        display_date: str = Query(None),
        keyword: str = Query(None),
        page: int = Query(1, ge=1),  # 当前页，默认是第一页
        per_page: int = Query(10, ge=1),  # 每页显示的条数，默认是10
        db: Session = Depends(get_db),
):
    translation = translations.get(lang)
    print(article_id, title, author, abstract, source_id, cum_issue, series, vol_no, page_no, search_date, display_date, keyword)
    # 如果没有任何查询条件，则返回空结果
    if not any([query, article_id, title, author, abstract, source_id, cum_issue, series, vol_no, page_no, search_date, display_date, keyword]):
        # 返回一个空结果
        return templates.TemplateResponse("search_results.html", {
            "request": request,
            "lang": lang,
            "translation": translation,
            "results": [],
            "no_results": True,
            "query": query,
            "current_page": page,
            "per_page": per_page,
            "total_pages": 0,
            "advanced_search": False
        })

    # 处理查询过滤器
    query_filter = db.query(Journal)
    # 处理搜索字段
    if query:
        query_filter = query_filter.filter(Journal.title.like(f"%{query}%"))
    if article_id:
        query_filter = query_filter.filter(Journal.article_id.like(f"%{article_id}%"))
    if title:
        query_filter = query_filter.filter(Journal.title.like(f"%{title}%"))
    if author:
        query_filter = query_filter.filter(Journal.author.like(f"%{author}%"))
    if abstract:
        query_filter = query_filter.filter(Journal.abstract.like(f"%{abstract}%"))
    if source_id:
        query_filter = query_filter.filter(Journal.source_id.like(f"%{source_id}%"))
    if cum_issue:
        query_filter = query_filter.filter(Journal.cum_issue.like(f"%{cum_issue}%"))
    if series:
        query_filter = query_filter.filter(Journal.series.like(f"%{series}%"))
    if vol_no:
        query_filter = query_filter.filter(Journal.vol_no.like(f"%{vol_no}%"))
    if page_no:
        query_filter = query_filter.filter(Journal.page_no.like(f"%{page_no}%"))
    if search_date:
        query_filter = query_filter.filter(Journal.search_date.like(f"%{search_date}%"))
    if display_date:
        query_filter = query_filter.filter(Journal.display_date.like(f"%{display_date}%"))
    if keyword:
        query_filter = query_filter.filter(Journal.keyword.like(f"%{keyword}%"))

    # 获取所有结果
    results = query_filter.all()

    # 分页处理
    total_results = len(results)
    total_pages = (total_results + per_page - 1) // per_page
    start = (page - 1) * per_page
    end = start + per_page
    paginated_results = results[start:end]

    # 判断是否有结果
    no_results = len(paginated_results) == 0

    return templates.TemplateResponse("search_results.html", {
        "request": request,
        "lang": lang,
        "translation": translation,
        "results": paginated_results,
        "no_results": no_results,
        "query": query,
        "current_page": page,
        "per_page": per_page,
        "total_results": total_results,
        "total_pages": total_pages,
        "advanced_search": True if query or any(
            [article_id, title, author, abstract, source_id, cum_issue, series, vol_no, page_no, search_date,
             display_date, keyword]) else False
    })




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
async def manual_upload_form(request: Request, lang: str = "zh_mo", success: Optional[bool] = False):
    translation = translations.get(lang)
    return templates.TemplateResponse("manual_upload.html", {
        "request": request,
        "translation": translation,
        "lang": lang,
        "success": success
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
    return RedirectResponse(url=f"/manual_upload?lang={lang}&success=true",  status_code=302)


# 使用HTTPBasic进行账户验证
security = HTTPBasic()


def authenticate_user(credentials: HTTPBasicCredentials = Depends(security)):
    if credentials.username != "admin" or credentials.password != "admin":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Basic"},
        )


@app.get("/log", response_class=HTMLResponse)
async def log_page(
        request: Request,
        lang: str = "zh_mo",
        page: int = Query(1, ge=1),
        per_page: int = Query(50, ge=1, le=300),
        db: Session = Depends(get_db),
        credentials: HTTPBasicCredentials = Depends(authenticate_user)
):
    translation = translations.get(lang)

    # 计算分页起始和结束位置
    offset = (page - 1) * per_page
    total_logs = db.query(UploadLog).count()  # 获取总日志数
    total_pages = (total_logs + per_page - 1) // per_page  # 计算总页数

    # 获取分页数据，包括上传时间
    logs = db.query(UploadLog).order_by(UploadLog.upload_time.desc()).offset(offset).limit(per_page).all()

    # 返回模板
    return templates.TemplateResponse("log.html", {
        "request": request,
        "translation": translation,
        "logs": logs,
        "total_pages": total_pages,
        "current_page": page,
        "per_page": per_page,
        "total_logs": total_logs,
        "lang": lang
    })
