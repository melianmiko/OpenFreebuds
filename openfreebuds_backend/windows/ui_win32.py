import winreg


def is_dark_taskbar():
    with winreg.OpenKey(
        winreg.HKEY_CURRENT_USER,
        r'Software\Microsoft\Windows\CurrentVersion\Themes\Personalize'
    ) as key:
        try:
            value, _ = winreg.QueryValueEx(key, "SystemUsesLightTheme")
            return value == 0
        except (FileNotFoundError, OSError):
            return False
