import re
from functools import partial

INTEGER_PATTERN = re.compile(r'^[1-9]\d*$')
USERNAME_PATTERN = re.compile(r'^[a-zA-Z0-9_\-\.]{6,20}$')
TEL_PATTERN = re.compile(r'^1[3-9]\d{9}$')
EMAIL_PATTERN = re.compile(
    r'^([a-zA-Z0-9_\-\.]+)'
    r'@((\[[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.)|'
    r'(([a-zA-Z0-9\-]+\.)+))([a-zA-Z]{2,4}|'
    r'[0-9]{1,3})(\]?)$', re.VERBOSE
)
URL_PATTERN = re.compile(
    r'^(?:http|ftp)s?://'
    r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|'
    r'localhost|'
    r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'
    r'(?::\d+)?'
    r'(?:/?|[/?]\S+)$', re.IGNORECASE
)


def check_with_pattern(pattern, value, *, hint=False):
    """使用正则表达式检查输入的值"""
    if hint:
        return '' if pattern.match(value) else f'{value} is invalid'
    else:
        return pattern.match(value)


check_integer = partial(check_with_pattern, INTEGER_PATTERN)
check_username = partial(check_with_pattern, USERNAME_PATTERN)
check_tel = partial(check_with_pattern, TEL_PATTERN)
check_email = partial(check_with_pattern, EMAIL_PATTERN)
check_url = partial(check_with_pattern, URL_PATTERN)
