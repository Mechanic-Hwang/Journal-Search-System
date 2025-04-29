import gettext
from fastapi import Request

def get_locale(request: Request) -> str:
    lang = request.query_params.get("lang")
    return lang if lang in ["zh_TW", "en", "pt"] else "zh_TW"

def get_translator(lang: str):
    return gettext.translation("messages", localedir="app/translations", languages=[lang], fallback=True)
