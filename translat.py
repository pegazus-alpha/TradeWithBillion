import i18n
import os

# Chemin vers le dossier des fichiers de langue
i18n.load_path.append(os.path.join(os.path.dirname(__file__), 'locales'))

# Définir la langue par défaut si la traduction est manquante
i18n.set('fallback', 'en')

# Format des clés (ex: "menu.infos")
i18n.set('filename_format', '{locale}.yml')

def tr(key: str, lang: str = "en") -> str:
    i18n.set('locale', lang)
    return i18n.t(key)
