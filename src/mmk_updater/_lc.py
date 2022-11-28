import locale

BASE_LOCALE = {
    "has_update_title": "New version of {} is available",
    "file_pattern": "File: {} ({})",
    "downloading": "Downloading file {}...",
    "downloading_run_after": "Installation will be started automatically after download",
    "download_btn": "Update now",
    "dl_error": "ERROR: Download failed",
    "close_btn": "Close",
    "site_btn": "View in web browser",
    "repo_install": "Install it via system package manager.",
    "manual_install": "Update downloaded, but we can't install it automatically.\nFile "
                      "was saved to {}.\nPlease install it after app close."
}

L18N = {
    "ru_RU": {
        "has_update_title": "Доступна новая версия {}",
        "file_pattern": "Будет загружен: {} ({})",
        "downloading": "Загружаем файл {}...",
        "downloading_run_after": "Установка начнётся сразу после загрузки",
        "download_btn": "Обновить",
        "dl_error": "ОШИБКА: Не удалось скачать файл",
        "site_btn": "Перейти на веб-сайт программы",
        "close_btn": "Закрыть",
        "repo_install": "Установите обновление ч-з системный пакетный менеджер",
        "manual_install": "Обновление загружено, но мы не можем установить его автоматически.\nФайл "
                          "сохранён по пути {}. \nУстановите его, когда будет возможность."
    }
}


def t(k):
    lang = locale.getdefaultlocale()[0]
    if lang in L18N:
        if k in L18N[lang]:
            return L18N[lang][k]

    if k in BASE_LOCALE:
        return BASE_LOCALE[k]
    return k
