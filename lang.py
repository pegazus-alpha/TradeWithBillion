import i18n
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# Configuration i18n
i18n.load_path.append('locales')
i18n.set('filename_format', '{locale}.{format}')
i18n.set('file_format', 'yml')
i18n.set('fallback', 'en')
i18n.set('enable_memoization', True)

def get_user_lang(update: Update) -> str:
    """Récupère la langue de l'utilisateur"""
    lang = update.effective_user.language_code
    if lang:
        return lang[:2].lower()
    return "en"

def set_user_locale(update: Update):
    """Définit la locale pour l'utilisateur actuel"""
    user_lang = get_user_lang(update)
    i18n.set('locale', user_lang)
    return user_lang