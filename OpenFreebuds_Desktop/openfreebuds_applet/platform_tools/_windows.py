import ctypes

RESULT_NO = 6
RESULT_YES = 7
MessageBox = ctypes.windll.user32.MessageBoxW


def show_message(message, window_title=""):
	MessageBox(None, message, window_title, 0)


def show_question(message, window_title=""):
	return MessageBox(None, message, window_title, 4)
