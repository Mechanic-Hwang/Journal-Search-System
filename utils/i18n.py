import gettext
from fastapi import Request

def get_locale(request: Request) -> str:
    lang = request.query_params.get("lang")
    return lang if lang in ["zh_mo", "en", "pt"] else "zh_mo"

def get_translator(lang: str):
    return gettext.translation("messages", localedir="app/translations", languages=[lang], fallback=True)
