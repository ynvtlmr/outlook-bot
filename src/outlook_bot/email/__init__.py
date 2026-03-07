"""Email client abstraction and parsing."""

from outlook_bot.email.client import EmailClient
from outlook_bot.email.outlook_mac import OutlookMacClient
from outlook_bot.email.parser import parse_raw_data
from outlook_bot.email.threading import group_into_threads

__all__ = ["EmailClient", "OutlookMacClient", "group_into_threads", "parse_raw_data"]
