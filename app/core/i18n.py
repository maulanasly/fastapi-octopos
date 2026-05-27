from typing import Optional

TRANSLATIONS = {
    "en": {
        "auth.invalid_credentials": "Could not validate credentials",
        "auth.user_not_found": "User not found",
        "auth.inactive_user": "Inactive user",
        "auth.insufficient_privileges": "The user doesn't have enough privileges",
    },
    "id": {
        "auth.invalid_credentials": "Kredensial tidak valid",
        "auth.user_not_found": "Pengguna tidak ditemukan",
        "auth.inactive_user": "Pengguna tidak aktif",
        "auth.insufficient_privileges": "Pengguna tidak memiliki hak akses yang cukup",
    },
}


def parse_language(accept_language: Optional[str], fallback: str = "en") -> str:
    if not accept_language:
        return fallback
    first = accept_language.split(",")[0].strip().lower().replace("-", "_")
    if first in TRANSLATIONS:
        return first
    base = first.split("_")[0]
    if base in TRANSLATIONS:
        return base
    return fallback


def t(key: str, language: str = "en", **kwargs) -> str:
    text = TRANSLATIONS.get(language, TRANSLATIONS["en"]).get(
        key, TRANSLATIONS["en"].get(key, key)
    )
    if kwargs:
        return text.format(**kwargs)
    return text
