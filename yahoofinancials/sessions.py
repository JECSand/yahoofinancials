import functools
from functools import lru_cache
from urllib3.util import Retry
import requests as requests
from requests import Session
from requests.adapters import HTTPAdapter
from requests.exceptions import ConnectionError, RetryError
from bs4 import BeautifulSoup
import datetime
import logging
from frozendict import frozendict
import threading
import random
from . import cache

DEFAULT_TIMEOUT = 5
cache_maxsize = 64

HEADERS = [
    {'upgrade-insecure-requests': '1', 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.114 Safari/537.36 Edg/89.0.774.76', 'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3', 'sec-ch-ua': 'Microsoft Edge;v="89", "Chromium";v="89", ";Not A Brand";v="99"', 'sec-ch-ua-mobile': '?0', 'sec-ch-ua-platform': 'Windows', 'sec-fetch-site': 'none', 'sec-fetch-mod': '', 'sec-fetch-user': '?1', 'accept-encoding': 'gzip', 'accept-language': 'en-US,es;q=0.6'},
    {'upgrade-insecure-requests': '1', 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.198 Safari/537.36 Edg/86.0.622.69', 'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8', 'sec-ch-ua': 'Microsoft Edge;v="86", "Chromium";v="86", ";Not A Brand";v="99"', 'sec-ch-ua-mobile': '?0', 'sec-ch-ua-platform': 'Windows', 'sec-fetch-site': 'none', 'sec-fetch-mod': '', 'sec-fetch-user': '?1', 'accept-encoding': 'gzip', 'accept-language': 'en-US,en;q=0.9,es;q=0.8'},
    {'upgrade-insecure-requests': '1', 'User-Agent': 'Mozilla/5.0 (Windows NT 6.3; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.93 Safari/537.36', 'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3', 'sec-ch-ua': 'Google Chrome;v="90", "Chromium";v="90", ";Not A Brand";v="99"', 'sec-ch-ua-mobile': '?0', 'sec-ch-ua-platform': 'Windows', 'sec-fetch-site': 'none', 'sec-fetch-mod': '', 'sec-fetch-user': '?1', 'accept-encoding': 'gzip, deflate', 'accept-language': 'en-US,en;q=0.9,it;q=0.8'},
    {'upgrade-insecure-requests': '1', 'User-Agent': 'Mozilla/5.0 (Windows NT 6.3; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.93 Safari/537.36', 'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3', 'sec-ch-ua': 'Google Chrome;v="90", "Chromium";v="90", ";Not A Brand";v="99"', 'sec-ch-ua-mobile': '?0', 'sec-ch-ua-platform': 'Windows', 'sec-fetch-site': 'none', 'sec-fetch-mod': '', 'sec-fetch-user': '?1', 'accept-encoding': 'gzip', 'accept-language': 'en-US,es;q=0.8'},
    {'upgrade-insecure-requests': '1', 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/73.0.3683.75 Safari/537.36', 'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3', 'sec-ch-ua': '" Not A;Brand";v="99", "Chromium";v="104", "Opera";v="90"', 'sec-ch-ua-mobile': '?0', 'sec-ch-ua-platform': '"Windows"', 'sec-fetch-site': 'none', 'sec-fetch-mod': '', 'sec-fetch-user': '?1', 'accept-encoding': 'gzip, deflate, br', 'accept-language': 'en'},
    {'upgrade-insecure-requests': '1', 'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.105 Safari/537.36', 'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8', 'sec-ch-ua': 'Google Chrome;v="84", "Chromium";v="84", ";Not A Brand";v="99"', 'sec-ch-ua-mobile': '?0', 'sec-ch-ua-platform': 'macOS', 'sec-fetch-site': 'none', 'sec-fetch-mod': '', 'sec-fetch-user': '?1', 'accept-encoding': 'gzip', 'accept-language': 'en-US,en;q=0.9,de;q=0.5'},
    {'upgrade-insecure-requests': '1x', 'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/72.0.3626.121 Safari/537.36', 'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3', 'sec-ch-ua': 'Google Chrome;v="72", "Chromium";v="72", ";Not A Brand";v="99"', 'sec-ch-ua-mobile': '?0', 'sec-ch-ua-platform': 'Windows', 'sec-fetch-site': 'none', 'sec-fetch-mod': '', 'sec-fetch-user': '?1', 'accept-encoding': 'gzip, deflate', 'accept-language': 'en-US,it;q=0.7'},
    {'upgrade-insecure-requests': '1', 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.121 Safari/537.36', 'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8', 'sec-ch-ua': 'Google Chrome;v="85", "Chromium";v="85", ";Not A Brand";v="99"', 'sec-ch-ua-mobile': '?0', 'sec-ch-ua-platform': 'Windows', 'sec-fetch-site': 'none', 'sec-fetch-mod': '', 'sec-fetch-user': '?1', 'accept-encoding': 'gzip, deflate', 'accept-language': 'en-US,es;q=0.6'},
    {'upgrade-insecure-requests': '1', 'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.114 Safari/537.36', 'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8', 'sec-ch-ua': 'Google Chrome;v="89", "Chromium";v="89", ";Not A Brand";v="99"', 'sec-ch-ua-mobile': '?0', 'sec-ch-ua-platform': 'macOS', 'sec-fetch-site': 'none', 'sec-fetch-mod': '', 'sec-fetch-user': '?1', 'accept-encoding': 'gzip, deflate', 'accept-language': 'en-US,es;q=0.7'},
    {'upgrade-insecure-requests': '1', 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.111 Safari/537.36', 'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8', 'sec-ch-ua': 'Google Chrome;v="86", "Chromium";v="86", ";Not A Brand";v="99"', 'sec-ch-ua-mobile': '?0', 'sec-ch-ua-platform': 'Windows', 'sec-fetch-site': 'none', 'sec-fetch-mod': '', 'sec-fetch-user': '?1', 'accept-encoding': 'gzip', 'accept-language': 'en-US,de;q=0.5'},
    {'upgrade-insecure-requests': '1', 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.85 Safari/537.36 Edg/90.0.818.46', 'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8', 'sec-ch-ua': 'Microsoft Edge;v="90", "Chromium";v="90", ";Not A Brand";v="99"', 'sec-ch-ua-mobile': '?0', 'sec-ch-ua-platform': 'Windows', 'sec-fetch-site': 'none', 'sec-fetch-mod': '', 'sec-fetch-user': '?1', 'accept-encoding': 'gzip', 'accept-language': 'en-US,it;q=0.8'},
    {'upgrade-insecure-requests': '1', 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.82 Safari/537.36', 'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8', 'sec-ch-ua': 'Google Chrome;v="89", "Chromium";v="89", ";Not A Brand";v="99"', 'sec-ch-ua-mobile': '?0', 'sec-ch-ua-platform': 'Windows', 'sec-fetch-site': 'none', 'sec-fetch-mod': '', 'sec-fetch-user': '?1', 'accept-encoding': 'gzip', 'accept-language': 'en-US,it;q=0.6'},
    {'upgrade-insecure-requests': '1', 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.182 Safari/537.36 Edg/88.0.705.74', 'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8', 'sec-ch-ua': 'Microsoft Edge;v="88", "Chromium";v="88", ";Not A Brand";v="99"', 'sec-ch-ua-mobile': '?0', 'sec-ch-ua-platform': 'Windows', 'sec-fetch-site': 'none', 'sec-fetch-mod': '', 'sec-fetch-user': '?1', 'accept-encoding': 'gzip', 'accept-language': 'en-US,en;q=0.9,es;q=0.5'},
    {'upgrade-insecure-requests': '1', 'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.116 Safari/537.36', 'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8', 'sec-ch-ua': 'Google Chrome;v="83", "Chromium";v="83", ";Not A Brand";v="99"', 'sec-ch-ua-mobile': '?0', 'sec-ch-ua-platform': 'macOS', 'sec-fetch-site': 'none', 'sec-fetch-mod': '', 'sec-fetch-user': '?1', 'accept-encoding': 'gzip', 'accept-language': 'en'},
    {'upgrade-insecure-requests': '1', 'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.105 Safari/537.36', 'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3', 'sec-ch-ua': 'Google Chrome;v="84", "Chromium";v="84", ";Not A Brand";v="99"', 'sec-ch-ua-mobile': '?0', 'sec-ch-ua-platform': 'macOS', 'sec-fetch-site': 'none', 'sec-fetch-mod': '', 'sec-fetch-user': '?1', 'accept-encoding': 'gzip, deflate', 'accept-language': 'en-US,de;q=0.9'},
    {'upgrade-insecure-requests': '1', 'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.90 Safari/537.36', 'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8', 'sec-ch-ua': 'Google Chrome;v="89", "Chromium";v="89", ";Not A Brand";v="99"', 'sec-ch-ua-mobile': '?0', 'sec-ch-ua-platform': 'Windows', 'sec-fetch-site': 'none', 'sec-fetch-mod': '', 'sec-fetch-user': '?1', 'accept-encoding': 'gzip', 'accept-language': 'en-US,en;q=0.9,fr;q=0.5'},
    {'upgrade-insecure-requests': '1', 'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36', 'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8', 'sec-ch-ua': 'Google Chrome;v="90", "Chromium";v="90", ";Not A Brand";v="99"', 'sec-ch-ua-mobile': '?0', 'sec-ch-ua-platform': 'macOS', 'sec-fetch-site': 'none', 'sec-fetch-mod': '', 'sec-fetch-user': '?1', 'accept-encoding': 'gzip', 'accept-language': 'en-US,es;q=0.8'},
    {'upgrade-insecure-requests': '1', 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.85 Safari/537.36', 'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8', 'sec-ch-ua': 'Google Chrome;v="90", "Chromium";v="90", ";Not A Brand";v="99"', 'sec-ch-ua-mobile': '?0', 'sec-ch-ua-platform': 'Windows', 'sec-fetch-site': 'none', 'sec-fetch-mod': '', 'sec-fetch-user': '?1', 'accept-encoding': 'gzip', 'accept-language': 'en-US,es;q=0.5'},
    {'upgrade-insecure-requests': '1', 'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 11_2_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.90 Safari/537.36', 'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8', 'sec-ch-ua': 'Google Chrome;v="89", "Chromium";v="89", ";Not A Brand";v="99"', 'sec-ch-ua-mobile': '?0', 'sec-ch-ua-platform': 'macOS', 'sec-fetch-site': 'none', 'sec-fetch-mod': '', 'sec-fetch-user': '?1', 'accept-encoding': 'gzip', 'accept-language': 'en-US,de;q=0.7'},
    {'upgrade-insecure-requests': '1', 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.182 Safari/537.36 Edg/88.0.705.81', 'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3', 'sec-ch-ua': 'Microsoft Edge;v="88", "Chromium";v="88", ";Not A Brand";v="99"', 'sec-ch-ua-mobile': '?0', 'sec-ch-ua-platform': 'Windows', 'sec-fetch-site': 'none', 'sec-fetch-mod': '', 'sec-fetch-user': '?1', 'accept-encoding': 'gzip', 'accept-language': 'en-US,it;q=0.6'},
    {'upgrade-insecure-requests': '1', 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.93 Safari/537.36', 'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3', 'sec-ch-ua': 'Google Chrome;v="90", "Chromium";v="90", ";Not A Brand";v="99"', 'sec-ch-ua-mobile': '?0', 'sec-ch-ua-platform': 'Windows', 'sec-fetch-site': 'none', 'sec-fetch-mod': '', 'sec-fetch-user': '?1', 'accept-encoding': 'gzip', 'accept-language': 'en-US,en;q=0.9,fr;q=0.5'},
    {'upgrade-insecure-requests': '1', 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.89 Safari/537.36', 'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8', 'sec-ch-ua': 'Google Chrome;v="84", "Chromium";v="84", ";Not A Brand";v="99"', 'sec-ch-ua-mobile': '?0', 'sec-ch-ua-platform': 'Windows', 'sec-fetch-site': 'none', 'sec-fetch-mod': '', 'sec-fetch-user': '?1', 'accept-encoding': 'gzip, deflate', 'accept-language': 'en-US,en;q=0.9,es;q=0.5'},
    {'upgrade-insecure-requests': '1', 'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.105 Safari/537.36', 'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8', 'sec-ch-ua': 'Google Chrome;v="84", "Chromium";v="84", ";Not A Brand";v="99"', 'sec-ch-ua-mobile': '?0', 'sec-ch-ua-platform': 'macOS', 'sec-fetch-site': 'none', 'sec-fetch-mod': '', 'sec-fetch-user': '?1', 'accept-encoding': 'gzip, deflate', 'accept-language': 'en-US'},
    {'upgrade-insecure-requests': '1', 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.61 Safari/537.36 Edg/83.0.478.37', 'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8', 'sec-ch-ua': 'Microsoft Edge;v="83", "Chromium";v="83", ";Not A Brand";v="99"', 'sec-ch-ua-mobile': '?0', 'sec-ch-ua-platform': 'Windows', 'sec-fetch-site': 'none', 'sec-fetch-mod': '', 'sec-fetch-user': '?1', 'accept-encoding': 'gzip, deflate', 'accept-language': 'en-US,de;q=0.8'},
    {'upgrade-insecure-requests': '1', 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.66 Safari/537.36', 'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8', 'sec-ch-ua': 'Google Chrome;v="87", "Chromium";v="87", ";Not A Brand";v="99"', 'sec-ch-ua-mobile': '?0', 'sec-ch-ua-platform': 'Windows', 'sec-fetch-site': 'none', 'sec-fetch-mod': '', 'sec-fetch-user': '?1', 'accept-encoding': 'gzip', 'accept-language': 'en-US,en;q=0.8'},
    {'upgrade-insecure-requests': '1', 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.182 Safari/537.36 Edg/88.0.705.81', 'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8', 'sec-ch-ua': 'Microsoft Edge;v="88", "Chromium";v="88", ";Not A Brand";v="99"', 'sec-ch-ua-mobile': '?0', 'sec-ch-ua-platform': 'Windows', 'sec-fetch-site': 'none', 'sec-fetch-mod': '', 'sec-fetch-user': '?1', 'accept-encoding': 'gzip', 'accept-language': 'en-US,it;q=0.6'},
    {'upgrade-insecure-requests': '1', 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.84 Safari/537.36', 'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3', 'sec-ch-ua': 'Google Chrome;v="63", "Chromium";v="63", ";Not A Brand";v="99"', 'sec-ch-ua-mobile': '?0', 'sec-ch-ua-platform': 'Windows', 'sec-fetch-site': 'none', 'sec-fetch-mod': '', 'sec-fetch-user': '?1', 'accept-encoding': 'gzip', 'accept-language': 'en'},
    {'upgrade-insecure-requests': '1', 'User-Agent': 'Mozilla/5.0 (Windows NT 6.3; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.93 Safari/537.36', 'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8', 'sec-ch-ua': 'Google Chrome;v="90", "Chromium";v="90", ";Not A Brand";v="99"', 'sec-ch-ua-mobile': '?0', 'sec-ch-ua-platform': 'Windows', 'sec-fetch-site': 'none', 'sec-fetch-mod': '', 'sec-fetch-user': '?1', 'accept-encoding': 'gzip', 'accept-language': 'en-US'},
    {'upgrade-insecure-requests': '1', 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.132 Safari/537.36', 'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8', 'sec-ch-ua': 'Google Chrome;v="80", "Chromium";v="80", ";Not A Brand";v="99"', 'sec-ch-ua-mobile': '?0', 'sec-ch-ua-platform': 'Windows', 'sec-fetch-site': 'none', 'sec-fetch-mod': '', 'sec-fetch-user': '?1', 'accept-encoding': 'gzip', 'accept-language': 'en-US,fr;q=0.7'},
    {'upgrade-insecure-requests': '1', 'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.192 Safari/537.36', 'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3', 'sec-ch-ua': 'Google Chrome;v="88", "Chromium";v="88", ";Not A Brand";v="99"', 'sec-ch-ua-mobile': '?0', 'sec-ch-ua-platform': 'macOS', 'sec-fetch-site': 'none', 'sec-fetch-mod': '', 'sec-fetch-user': '?1', 'accept-encoding': 'gzip', 'accept-language': 'en-US,en;q=0.9,de;q=0.8'},
    {'upgrade-insecure-requests': '1', 'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; ) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.116 Safari/537.36', 'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3', 'sec-ch-ua': 'Google Chrome;v="83", "Chromium";v="83", ";Not A Brand";v="99"', 'sec-ch-ua-mobile': '?0', 'sec-ch-ua-platform': 'Windows', 'sec-fetch-site': 'none', 'sec-fetch-mod': '', 'sec-fetch-user': '?1', 'accept-encoding': 'gzip, deflate', 'accept-language': 'en-US,es;q=0.6'},
    {'upgrade-insecure-requests': '1', 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.182 Safari/537.36', 'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8', 'sec-ch-ua': 'Google Chrome;v="88", "Chromium";v="88", ";Not A Brand";v="99"', 'sec-ch-ua-mobile': '?0', 'sec-ch-ua-platform': 'Windows', 'sec-fetch-site': 'none', 'sec-fetch-mod': '', 'sec-fetch-user': '?1', 'accept-encoding': 'gzip, deflate', 'accept-language': 'en-US,it;q=0.5'},
    {'upgrade-insecure-requests': '1', 'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.93 Safari/537.36', 'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3', 'sec-ch-ua': 'Google Chrome;v="90", "Chromium";v="90", ";Not A Brand";v="99"', 'sec-ch-ua-mobile': '?0', 'sec-ch-ua-platform': 'Windows', 'sec-fetch-site': 'none', 'sec-fetch-mod': '', 'sec-fetch-user': '?1', 'accept-encoding': 'gzip', 'accept-language': 'en-US,en;q=0.9,fr;q=0.8'},
    {'upgrade-insecure-requests': '1', 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.72 Safari/537.36 Edg/90.0.818.42', 'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8', 'sec-ch-ua': 'Microsoft Edge;v="90", "Chromium";v="90", ";Not A Brand";v="99"', 'sec-ch-ua-mobile': '?0', 'sec-ch-ua-platform': 'Windows', 'sec-fetch-site': 'none', 'sec-fetch-mod': '', 'sec-fetch-user': '?1', 'accept-encoding': 'gzip, deflate', 'accept-language': 'en-US,en;q=0.8'},
    {'upgrade-insecure-requests': '1', 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.90 Safari/537.36 Edg/89.0.774.57', 'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3', 'sec-ch-ua': 'Microsoft Edge;v="89", "Chromium";v="89", ";Not A Brand";v="99"', 'sec-ch-ua-mobile': '?0', 'sec-ch-ua-platform': 'Windows', 'sec-fetch-site': 'none', 'sec-fetch-mod': '', 'sec-fetch-user': '?1', 'accept-encoding': 'gzip, deflate', 'accept-language': 'en-US'},
    {'upgrade-insecure-requests': '1', 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.102 Safari/537.36', 'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3', 'sec-ch-ua': 'Google Chrome;v="70", "Chromium";v="70", ";Not A Brand";v="99"', 'sec-ch-ua-mobile': '?0', 'sec-ch-ua-platform': 'Windows', 'sec-fetch-site': 'none', 'sec-fetch-mod': '', 'sec-fetch-user': '?1', 'accept-encoding': 'gzip, deflate', 'accept-language': 'en-US,en;q=0.8'},
    {'upgrade-insecure-requests': '1', 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.132 Safari/537.36', 'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3', 'sec-ch-ua': 'Google Chrome;v="80", "Chromium";v="80", ";Not A Brand";v="99"', 'sec-ch-ua-mobile': '?0', 'sec-ch-ua-platform': 'Windows', 'sec-fetch-site': 'none', 'sec-fetch-mod': '', 'sec-fetch-user': '?1', 'accept-encoding': 'gzip, deflate', 'accept-language': 'en-US,fr;q=0.5'},
    {'upgrade-insecure-requests': '1', 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.85 Safari/537.36 Edg/90.0.818.46', 'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3', 'sec-ch-ua': 'Microsoft Edge;v="90", "Chromium";v="90", ";Not A Brand";v="99"', 'sec-ch-ua-mobile': '?0', 'sec-ch-ua-platform': 'Windows', 'sec-fetch-site': 'none', 'sec-fetch-mod': '', 'sec-fetch-user': '?1', 'accept-encoding': 'gzip', 'accept-language': 'en-US,it;q=0.6'},
    {'upgrade-insecure-requests': '1', 'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.198 Safari/537.36', 'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8', 'sec-ch-ua': 'Google Chrome;v="86", "Chromium";v="86", ";Not A Brand";v="99"', 'sec-ch-ua-mobile': '?0', 'sec-ch-ua-platform': 'macOS', 'sec-fetch-site': 'none', 'sec-fetch-mod': '', 'sec-fetch-user': '?1', 'accept-encoding': 'gzip, deflate', 'accept-language': 'en-US,en;q=0.7'},
    {'upgrade-insecure-requests': '1', 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.132 Safari/537.36', 'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3', 'sec-ch-ua': 'Google Chrome;v="80", "Chromium";v="80", ";Not A Brand";v="99"', 'sec-ch-ua-mobile': '?0', 'sec-ch-ua-platform': 'Windows', 'sec-fetch-site': 'none', 'sec-fetch-mod': '', 'sec-fetch-user': '?1', 'accept-encoding': 'gzip', 'accept-language': 'en-US,fr;q=0.5'},
    {'upgrade-insecure-requests': '1', 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.67 Safari/537.36 Edg/87.0.664.52', 'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8', 'sec-ch-ua': 'Microsoft Edge;v="87", "Chromium";v="87", ";Not A Brand";v="99"', 'sec-ch-ua-mobile': '?0', 'sec-ch-ua-platform': 'Windows', 'sec-fetch-site': 'none', 'sec-fetch-mod': '', 'sec-fetch-user': '?1', 'accept-encoding': 'gzip, deflate', 'accept-language': 'en-US,en;q=0.9,es;q=0.5'},
    {'upgrade-insecure-requests': '1', 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.93 Safari/537.36', 'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8', 'sec-ch-ua': 'Google Chrome;v="90", "Chromium";v="90", ";Not A Brand";v="99"', 'sec-ch-ua-mobile': '?0', 'sec-ch-ua-platform': 'Windows', 'sec-fetch-site': 'none', 'sec-fetch-mod': '', 'sec-fetch-user': '?1', 'accept-encoding': 'gzip', 'accept-language': 'en-US,en;q=0.9,de;q=0.5'},
    {'upgrade-insecure-requests': '1', 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.111 Safari/537.36', 'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8', 'sec-ch-ua': 'Google Chrome;v="86", "Chromium";v="86", ";Not A Brand";v="99"', 'sec-ch-ua-mobile': '?0', 'sec-ch-ua-platform': 'Windows', 'sec-fetch-site': 'none', 'sec-fetch-mod': '', 'sec-fetch-user': '?1', 'accept-encoding': 'gzip, deflate', 'accept-language': 'en-US,en;q=0.9,it;q=0.5'},
    {'upgrade-insecure-requests': '1', 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.61 Safari/537.36 Edg/83.0.478.37', 'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3', 'sec-ch-ua': 'Microsoft Edge;v="83", "Chromium";v="83", ";Not A Brand";v="99"', 'sec-ch-ua-mobile': '?0', 'sec-ch-ua-platform': 'Windows', 'sec-fetch-site': 'none', 'sec-fetch-mod': '', 'sec-fetch-user': '?1', 'accept-encoding': 'gzip, deflate', 'accept-language': 'en-US,de;q=0.9'},
    {'upgrade-insecure-requests': '1', 'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.83 Safari/537.36', 'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3', 'sec-ch-ua': 'Google Chrome;v="85", "Chromium";v="85", ";Not A Brand";v="99"', 'sec-ch-ua-mobile': '?0', 'sec-ch-ua-platform': 'macOS', 'sec-fetch-site': 'none', 'sec-fetch-mod': '', 'sec-fetch-user': '?1', 'accept-encoding': 'gzip, deflate', 'accept-language': 'en-US'},
    {'upgrade-insecure-requests': '1', 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.87 Safari/537.36', 'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8', 'sec-ch-ua': 'Google Chrome;v="55", "Chromium";v="55", ";Not A Brand";v="99"', 'sec-ch-ua-mobile': '?0', 'sec-ch-ua-platform': 'Windows', 'sec-fetch-site': 'none', 'sec-fetch-mod': '', 'sec-fetch-user': '?1', 'accept-encoding': 'gzip', 'accept-language': 'en-US,en;q=0.6'},
    {'upgrade-insecure-requests': '1', 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/52.0.2743.116 Safari/537.36 Edge/15.15063', 'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8', 'sec-ch-ua': 'Google Chrome;v="95", "Chromium";v="95", ";Not A Brand";v="99"', 'sec-ch-ua-mobile': '?0', 'sec-ch-ua-platform': 'Windows', 'sec-fetch-site': 'none', 'sec-fetch-mod': '', 'sec-fetch-user': '?1', 'accept-encoding': 'gzip, deflate', 'accept-language': 'en-US,it;q=0.9'},
    {'upgrade-insecure-requests': '1', 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.114 Safari/537.36 Edg/89.0.774.68', 'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8', 'sec-ch-ua': 'Microsoft Edge;v="89", "Chromium";v="89", ";Not A Brand";v="99"', 'sec-ch-ua-mobile': '?0', 'sec-ch-ua-platform': 'Windows', 'sec-fetch-site': 'none', 'sec-fetch-mod': '', 'sec-fetch-user': '?1', 'accept-encoding': 'gzip, deflate', 'accept-language': 'en-US,es;q=0.6'},
    {'upgrade-insecure-requests': '1', 'User-Agent': 'Mozilla/5.0 (Windows NT 6.2; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.198 Safari/537.36', 'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3', 'sec-ch-ua': 'Google Chrome;v="86", "Chromium";v="86", ";Not A Brand";v="99"', 'sec-ch-ua-mobile': '?0', 'sec-ch-ua-platform': 'Windows', 'sec-fetch-site': 'none', 'sec-fetch-mod': '', 'sec-fetch-user': '?1', 'accept-encoding': 'gzip, deflate', 'accept-language': 'en-US,fr;q=0.8'},
    {'upgrade-insecure-requests': '1', 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.116 Safari/537.36', 'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8', 'sec-ch-ua': 'Google Chrome;v="83", "Chromium";v="83", ";Not A Brand";v="99"', 'sec-ch-ua-mobile': '?0', 'sec-ch-ua-platform': 'Windows', 'sec-fetch-site': 'none', 'sec-fetch-mod': '', 'sec-fetch-user': '?1', 'accept-encoding': 'gzip', 'accept-language': 'en'},
    {'upgrade-insecure-requests': '1', 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.85 Safari/537.36 Edg/90.0.818.46', 'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8', 'sec-ch-ua': 'Microsoft Edge;v="90", "Chromium";v="90", ";Not A Brand";v="99"', 'sec-ch-ua-mobile': '?0', 'sec-ch-ua-platform': 'Windows', 'sec-fetch-site': 'none', 'sec-fetch-mod': '', 'sec-fetch-user': '?1', 'accept-encoding': 'gzip', 'accept-language': 'en'},
    {'upgrade-insecure-requests': '1', 'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; ) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.116 Safari/537.36', 'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3', 'sec-ch-ua': 'Google Chrome;v="83", "Chromium";v="83", ";Not A Brand";v="99"', 'sec-ch-ua-mobile': '?0', 'sec-ch-ua-platform': 'Windows', 'sec-fetch-site': 'none', 'sec-fetch-mod': '', 'sec-fetch-user': '?1', 'accept-encoding': 'gzip', 'accept-language': 'en-US,en;q=0.9,de;q=0.5'},
    {'upgrade-insecure-requests': '1', 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.82 Safari/537.36 Edg/89.0.774.50', 'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8', 'sec-ch-ua': 'Microsoft Edge;v="89", "Chromium";v="89", ";Not A Brand";v="99"', 'sec-ch-ua-mobile': '?0', 'sec-ch-ua-platform': 'Windows', 'sec-fetch-site': 'none', 'sec-fetch-mod': '', 'sec-fetch-user': '?1', 'accept-encoding': 'gzip, deflate', 'accept-language': 'en-US,fr;q=0.8'},
    {'upgrade-insecure-requests': '1', 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.121 Safari/537.36', 'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8', 'sec-ch-ua': 'Google Chrome;v="85", "Chromium";v="85", ";Not A Brand";v="99"', 'sec-ch-ua-mobile': '?0', 'sec-ch-ua-platform': 'Windows', 'sec-fetch-site': 'none', 'sec-fetch-mod': '', 'sec-fetch-user': '?1', 'accept-encoding': 'gzip', 'accept-language': 'en-US,de;q=0.7'},
    {'upgrade-insecure-requests': '1', 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.88 Safari/537.36', 'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3', 'sec-ch-ua': 'Google Chrome;v="87", "Chromium";v="87", ";Not A Brand";v="99"', 'sec-ch-ua-mobile': '?0', 'sec-ch-ua-platform': 'Windows', 'sec-fetch-site': 'none', 'sec-fetch-mod': '', 'sec-fetch-user': '?1', 'accept-encoding': 'gzip', 'accept-language': 'en'},
    {'upgrade-insecure-requests': '1', 'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.135 Safari/537.36', 'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3', 'sec-ch-ua': 'Google Chrome;v="84", "Chromium";v="84", ";Not A Brand";v="99"', 'sec-ch-ua-mobile': '?0', 'sec-ch-ua-platform': 'macOS', 'sec-fetch-site': 'none', 'sec-fetch-mod': '', 'sec-fetch-user': '?1', 'accept-encoding': 'gzip', 'accept-language': 'en-US,en;q=0.9,it;q=0.8'},
    {'upgrade-insecure-requests': '1', 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.82 Safari/537.36', 'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3', 'sec-ch-ua': 'Google Chrome;v="89", "Chromium";v="89", ";Not A Brand";v="99"', 'sec-ch-ua-mobile': '?0', 'sec-ch-ua-platform': 'Windows', 'sec-fetch-site': 'none', 'sec-fetch-mod': '', 'sec-fetch-user': '?1', 'accept-encoding': 'gzip', 'accept-language': 'en-US'},
    {'upgrade-insecure-requests': '1', 'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 11_2_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.90 Safari/537.36', 'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8', 'sec-ch-ua': 'Google Chrome;v="89", "Chromium";v="89", ";Not A Brand";v="99"', 'sec-ch-ua-mobile': '?0', 'sec-ch-ua-platform': 'macOS', 'sec-fetch-site': 'none', 'sec-fetch-mod': '', 'sec-fetch-user': '?1', 'accept-encoding': 'gzip, deflate', 'accept-language': 'en-US'},
    {'upgrade-insecure-requests': '1', 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/52.0.2743.116 Safari/537.36 Edge/15.15063', 'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8', 'sec-ch-ua': 'Google Chrome;v="95", "Chromium";v="95", ";Not A Brand";v="99"', 'sec-ch-ua-mobile': '?0', 'sec-ch-ua-platform': 'Windows', 'sec-fetch-site': 'none', 'sec-fetch-mod': '', 'sec-fetch-user': '?1', 'accept-encoding': 'gzip, deflate', 'accept-language': 'en-US,en;q=0.5'},
    {'upgrade-insecure-requests': '1', 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.125 Safari/537.36', 'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8', 'sec-ch-ua': 'Google Chrome;v="84", "Chromium";v="84", ";Not A Brand";v="99"', 'sec-ch-ua-mobile': '?0', 'sec-ch-ua-platform': 'Windows', 'sec-fetch-site': 'none', 'sec-fetch-mod': '', 'sec-fetch-user': '?1', 'accept-encoding': 'gzip, deflate', 'accept-language': 'en-US,en;q=0.9,it;q=0.5'},
    {'upgrade-insecure-requests': '1', 'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.114 Safari/537.36', 'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8', 'sec-ch-ua': 'Google Chrome;v="89", "Chromium";v="89", ";Not A Brand";v="99"', 'sec-ch-ua-mobile': '?0', 'sec-ch-ua-platform': 'macOS', 'sec-fetch-site': 'none', 'sec-fetch-mod': '', 'sec-fetch-user': '?1', 'accept-encoding': 'gzip', 'accept-language': 'en-US,it;q=0.9'},
    {'upgrade-insecure-requests': '1', 'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.93 Safari/537.36', 'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8', 'sec-ch-ua': 'Google Chrome;v="90", "Chromium";v="90", ";Not A Brand";v="99"', 'sec-ch-ua-mobile': '?0', 'sec-ch-ua-platform': 'macOS', 'sec-fetch-site': 'none', 'sec-fetch-mod': '', 'sec-fetch-user': '?1', 'accept-encoding': 'gzip, deflate', 'accept-language': 'en-US,en;q=0.9,de;q=0.8'},
    {'upgrade-insecure-requests': '1', 'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.105 Safari/537.36', 'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8', 'sec-ch-ua': '" Not A;Brand";v="99", "Chromium";v="104", "Opera";v="90"', 'sec-ch-ua-mobile': '?0', 'sec-ch-ua-platform': '"Windows"', 'sec-fetch-site': 'none', 'sec-fetch-mod': '', 'sec-fetch-user': '?1', 'accept-encoding': 'gzip, deflate, br', 'accept-language': 'en'},
    {'upgrade-insecure-requests': '1', 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.182 Safari/537.36 Edg/88.0.705.74', 'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3', 'sec-ch-ua': 'Microsoft Edge;v="88", "Chromium";v="88", ";Not A Brand";v="99"', 'sec-ch-ua-mobile': '?0', 'sec-ch-ua-platform': 'Windows', 'sec-fetch-site': 'none', 'sec-fetch-mod': '', 'sec-fetch-user': '?1', 'accept-encoding': 'gzip, deflate', 'accept-language': 'en-US,en;q=0.9,es;q=0.8'},
    {'upgrade-insecure-requests': '1', 'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.93 Safari/537.36', 'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3', 'sec-ch-ua': '" Not A;Brand";v="99", "Chromium";v="100", "Google Chrome";v="100"', 'sec-ch-ua-mobile': '?0', 'sec-ch-ua-platform': '"Windows"', 'sec-fetch-site': 'none', 'sec-fetch-mod': '', 'sec-fetch-user': '?1', 'accept-encoding': 'gzip, deflate, br', 'accept-language': 'en-US,fr;q=0.7'},
    {'upgrade-insecure-requests': '1', 'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.135 Safari/537.36', 'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8', 'sec-ch-ua': 'Google Chrome;v="84", "Chromium";v="84", ";Not A Brand";v="99"', 'sec-ch-ua-mobile': '?0', 'sec-ch-ua-platform': 'macOS', 'sec-fetch-site': 'none', 'sec-fetch-mod': '', 'sec-fetch-user': '?1', 'accept-encoding': 'gzip, deflate', 'accept-language': 'en-US,es;q=0.7'},
    {'upgrade-insecure-requests': '1', 'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.106 Safari/537.36', 'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3', 'sec-ch-ua': 'Google Chrome;v="80", "Chromium";v="80", ";Not A Brand";v="99"', 'sec-ch-ua-mobile': '?0', 'sec-ch-ua-platform': 'Windows', 'sec-fetch-site': 'none', 'sec-fetch-mod': '', 'sec-fetch-user': '?1', 'accept-encoding': 'gzip, deflate', 'accept-language': 'en'},
    {'upgrade-insecure-requests': '1', 'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.198 Safari/537.36', 'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3', 'sec-ch-ua': 'Google Chrome;v="86", "Chromium";v="86", ";Not A Brand";v="99"', 'sec-ch-ua-mobile': '?0', 'sec-ch-ua-platform': 'macOS', 'sec-fetch-site': 'none', 'sec-fetch-mod': '', 'sec-fetch-user': '?1', 'accept-encoding': 'gzip', 'accept-language': 'en-US,de;q=0.6'},
    {'upgrade-insecure-requests': '1', 'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.150 Safari/537.36', 'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8', 'sec-ch-ua': 'Google Chrome;v="88", "Chromium";v="88", ";Not A Brand";v="99"', 'sec-ch-ua-mobile': '?0', 'sec-ch-ua-platform': 'macOS', 'sec-fetch-site': 'none', 'sec-fetch-mod': '', 'sec-fetch-user': '?1', 'accept-encoding': 'gzip, deflate', 'accept-language': 'en-US,en;q=0.9,de;q=0.5'},
    {'upgrade-insecure-requests': '1', 'User-Agent': 'Mozilla/5.0 (Windows NT 6.3; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.61 Safari/537.36', 'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3', 'sec-ch-ua': 'Google Chrome;v="83", "Chromium";v="83", ";Not A Brand";v="99"', 'sec-ch-ua-mobile': '?0', 'sec-ch-ua-platform': 'Windows', 'sec-fetch-site': 'none', 'sec-fetch-mod': '', 'sec-fetch-user': '?1', 'accept-encoding': 'gzip, deflate', 'accept-language': 'en-US,de;q=0.7'},
    {'upgrade-insecure-requests': '1', 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.136 Safari/537.36', 'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3', 'sec-ch-ua': 'Google Chrome;v="79", "Chromium";v="79", ";Not A Brand";v="99"', 'sec-ch-ua-mobile': '?0', 'sec-ch-ua-platform': 'Windows', 'sec-fetch-site': 'none', 'sec-fetch-mod': '', 'sec-fetch-user': '?1', 'accept-encoding': 'gzip, deflate', 'accept-language': 'en-US,en;q=0.6'},
    {'upgrade-insecure-requests': '1', 'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.106 Safari/537.36', 'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3', 'sec-ch-ua': 'Google Chrome;v="83", "Chromium";v="83", ";Not A Brand";v="99"', 'sec-ch-ua-mobile': '?0', 'sec-ch-ua-platform': 'Windows', 'sec-fetch-site': 'none', 'sec-fetch-mod': '', 'sec-fetch-user': '?1', 'accept-encoding': 'gzip, deflate', 'accept-language': 'en-US'},
    {'upgrade-insecure-requests': '1', 'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.105 Safari/537.36', 'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3', 'sec-ch-ua': 'Google Chrome;v="84", "Chromium";v="84", ";Not A Brand";v="99"', 'sec-ch-ua-mobile': '?0', 'sec-ch-ua-platform': 'macOS', 'sec-fetch-site': 'none', 'sec-fetch-mod': '', 'sec-fetch-user': '?1', 'accept-encoding': 'gzip', 'accept-language': 'en-US,en;q=0.9,fr;q=0.8'},
    {'upgrade-insecure-requests': '1', 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.114 Safari/537.36', 'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3', 'sec-ch-ua': 'Google Chrome;v="89", "Chromium";v="89", ";Not A Brand";v="99"', 'sec-ch-ua-mobile': '?0', 'sec-ch-ua-platform': 'Windows', 'sec-fetch-site': 'none', 'sec-fetch-mod': '', 'sec-fetch-user': '?1', 'accept-encoding': 'gzip, deflate', 'accept-language': 'en-US,de;q=0.7'},
    {'upgrade-insecure-requests': '1', 'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.105 Safari/537.36', 'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3', 'sec-ch-ua': 'Google Chrome;v="84", "Chromium";v="84", ";Not A Brand";v="99"', 'sec-ch-ua-mobile': '?0', 'sec-ch-ua-platform': 'macOS', 'sec-fetch-site': 'none', 'sec-fetch-mod': '', 'sec-fetch-user': '?1', 'accept-encoding': 'gzip, deflate', 'accept-language': 'en-US,en;q=0.5'},
    {'upgrade-insecure-requests': '1', 'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.114 Safari/537.36', 'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3', 'sec-ch-ua': 'Google Chrome;v="89", "Chromium";v="89", ";Not A Brand";v="99"', 'sec-ch-ua-mobile': '?0', 'sec-ch-ua-platform': 'Windows', 'sec-fetch-site': 'none', 'sec-fetch-mod': '', 'sec-fetch-user': '?1', 'accept-encoding': 'gzip, deflate', 'accept-language': 'en-US,es;q=0.8'},
    {'upgrade-insecure-requests': '1', 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.89 Safari/537.36', 'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8', 'sec-ch-ua': 'Google Chrome;v="84", "Chromium";v="84", ";Not A Brand";v="99"', 'sec-ch-ua-mobile': '?0', 'sec-ch-ua-platform': 'Windows', 'sec-fetch-site': 'none', 'sec-fetch-mod': '', 'sec-fetch-user': '?1', 'accept-encoding': 'gzip', 'accept-language': 'en-US,en;q=0.7'},
    {'upgrade-insecure-requests': '1', 'User-Agent': 'Mozilla/5.0 (Windows NT 6.3; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.93 Safari/537.36', 'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8', 'sec-ch-ua': 'Google Chrome;v="90", "Chromium";v="90", ";Not A Brand";v="99"', 'sec-ch-ua-mobile': '?0', 'sec-ch-ua-platform': 'Windows', 'sec-fetch-site': 'none', 'sec-fetch-mod': '', 'sec-fetch-user': '?1', 'accept-encoding': 'gzip, deflate', 'accept-language': 'en-US,it;q=0.6'},
    {'upgrade-insecure-requests': '1', 'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.93 Safari/537.36', 'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8', 'sec-ch-ua': 'Google Chrome;v="90", "Chromium";v="90", ";Not A Brand";v="99"', 'sec-ch-ua-mobile': '?0', 'sec-ch-ua-platform': 'Windows', 'sec-fetch-site': 'none', 'sec-fetch-mod': '', 'sec-fetch-user': '?1', 'accept-encoding': 'gzip', 'accept-language': 'en-US,it;q=0.8'},
    {'upgrade-insecure-requests': '1', 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.121 Safari/537.36 Edg/85.0.564.70', 'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3', 'sec-ch-ua': 'Microsoft Edge;v="85", "Chromium";v="85", ";Not A Brand";v="99"', 'sec-ch-ua-mobile': '?0', 'sec-ch-ua-platform': 'Windows', 'sec-fetch-site': 'none', 'sec-fetch-mod': '', 'sec-fetch-user': '?1', 'accept-encoding': 'gzip', 'accept-language': 'en-US,en;q=0.9,de;q=0.5'},
    {'upgrade-insecure-requests': '1', 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.67 Safari/537.36 Edg/87.0.664.47', 'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8', 'sec-ch-ua': 'Microsoft Edge;v="87", "Chromium";v="87", ";Not A Brand";v="99"', 'sec-ch-ua-mobile': '?0', 'sec-ch-ua-platform': 'Windows', 'sec-fetch-site': 'none', 'sec-fetch-mod': '', 'sec-fetch-user': '?1', 'accept-encoding': 'gzip', 'accept-language': 'en'},
    {'upgrade-insecure-requests': '1', 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.93 Safari/537.36 Edg/90.0.818.56', 'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8', 'sec-ch-ua': 'Microsoft Edge;v="90", "Chromium";v="90", ";Not A Brand";v="99"', 'sec-ch-ua-mobile': '?0', 'sec-ch-ua-platform': 'Windows', 'sec-fetch-site': 'none', 'sec-fetch-mod': '', 'sec-fetch-user': '?1', 'accept-encoding': 'gzip', 'accept-language': 'en-US,it;q=0.7'},
    {'upgrade-insecure-requests': '1', 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.135 Safari/537.36', 'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8', 'sec-ch-ua': 'Google Chrome;v="84", "Chromium";v="84", ";Not A Brand";v="99"', 'sec-ch-ua-mobile': '?0', 'sec-ch-ua-platform': 'Windows', 'sec-fetch-site': 'none', 'sec-fetch-mod': '', 'sec-fetch-user': '?1', 'accept-encoding': 'gzip, deflate', 'accept-language': 'en-US,en;q=0.9,fr;q=0.8'},
    {'upgrade-insecure-requests': '1', 'User-Agent': 'Mozilla/5.0 (Windows NT 6.3; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.190 Safari/537.36', 'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8', 'sec-ch-ua': 'Google Chrome;v="88", "Chromium";v="88", ";Not A Brand";v="99"', 'sec-ch-ua-mobile': '?0', 'sec-ch-ua-platform': 'Windows', 'sec-fetch-site': 'none', 'sec-fetch-mod': '', 'sec-fetch-user': '?1', 'accept-encoding': 'gzip', 'accept-language': 'en-US,fr;q=0.8'},
    {'upgrade-insecure-requests': '1', 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.85 Safari/537.36 Edg/90.0.818.49', 'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3', 'sec-ch-ua': 'Microsoft Edge;v="90", "Chromium";v="90", ";Not A Brand";v="99"', 'sec-ch-ua-mobile': '?0', 'sec-ch-ua-platform': 'Windows', 'sec-fetch-site': 'none', 'sec-fetch-mod': '', 'sec-fetch-user': '?1', 'accept-encoding': 'gzip', 'accept-language': 'en-US,de;q=0.6'},
    {'upgrade-insecure-requests': '1', 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.116 Safari/537.36', 'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8', 'sec-ch-ua': 'Google Chrome;v="83", "Chromium";v="83", ";Not A Brand";v="99"', 'sec-ch-ua-mobile': '?0', 'sec-ch-ua-platform': 'Windows', 'sec-fetch-site': 'none', 'sec-fetch-mod': '', 'sec-fetch-user': '?1', 'accept-encoding': 'gzip', 'accept-language': 'en-US,es;q=0.8'},
    {'upgrade-insecure-requests': '1', 'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.198 Safari/537.36', 'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8', 'sec-ch-ua': 'Google Chrome;v="86", "Chromium";v="86", ";Not A Brand";v="99"', 'sec-ch-ua-mobile': '?0', 'sec-ch-ua-platform': 'macOS', 'sec-fetch-site': 'none', 'sec-fetch-mod': '', 'sec-fetch-user': '?1', 'accept-encoding': 'gzip, deflate', 'accept-language': 'en-US,es;q=0.8'},
    {'upgrade-insecure-requests': '1', 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.141 Safari/537.36 Edg/87.0.664.75', 'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8', 'sec-ch-ua': 'Microsoft Edge;v="87", "Chromium";v="87", ";Not A Brand";v="99"', 'sec-ch-ua-mobile': '?0', 'sec-ch-ua-platform': 'Windows', 'sec-fetch-site': 'none', 'sec-fetch-mod': '', 'sec-fetch-user': '?1', 'accept-encoding': 'gzip', 'accept-language': 'en-US,de;q=0.8'},
    {'upgrade-insecure-requests': '1', 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.72 Safari/537.36', 'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3', 'sec-ch-ua': 'Google Chrome;v="89", "Chromium";v="89", ";Not A Brand";v="99"', 'sec-ch-ua-mobile': '?0', 'sec-ch-ua-platform': 'Windows', 'sec-fetch-site': 'none', 'sec-fetch-mod': '', 'sec-fetch-user': '?1', 'accept-encoding': 'gzip, deflate', 'accept-language': 'en-US'},
    {'upgrade-insecure-requests': '1', 'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.198 Safari/537.36', 'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8', 'sec-ch-ua': 'Google Chrome;v="86", "Chromium";v="86", ";Not A Brand";v="99"', 'sec-ch-ua-mobile': '?0', 'sec-ch-ua-platform': 'macOS', 'sec-fetch-site': 'none', 'sec-fetch-mod': '', 'sec-fetch-user': '?1', 'accept-encoding': 'gzip', 'accept-language': 'en-US,it;q=0.7'},
    {'upgrade-insecure-requests': '1', 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.67 Safari/537.36 Edg/87.0.664.52', 'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8', 'sec-ch-ua': 'Microsoft Edge;v="87", "Chromium";v="87", ";Not A Brand";v="99"', 'sec-ch-ua-mobile': '?0', 'sec-ch-ua-platform': 'Windows', 'sec-fetch-site': 'none', 'sec-fetch-mod': '', 'sec-fetch-user': '?1', 'accept-encoding': 'gzip', 'accept-language': 'en-US,it;q=0.9'},
    {'upgrade-insecure-requests': '1', 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.90 Safari/537.36', 'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3', 'sec-ch-ua': 'Google Chrome;v="89", "Chromium";v="89", ";Not A Brand";v="99"', 'sec-ch-ua-mobile': '?0', 'sec-ch-ua-platform': 'Windows', 'sec-fetch-site': 'none', 'sec-fetch-mod': '', 'sec-fetch-user': '?1', 'accept-encoding': 'gzip', 'accept-language': 'en-US'},
    {'upgrade-insecure-requests': '1', 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.121 Safari/537.36 Edg/85.0.564.70', 'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3', 'sec-ch-ua': 'Microsoft Edge;v="85", "Chromium";v="85", ";Not A Brand";v="99"', 'sec-ch-ua-mobile': '?0', 'sec-ch-ua-platform': 'Windows', 'sec-fetch-site': 'none', 'sec-fetch-mod': '', 'sec-fetch-user': '?1', 'accept-encoding': 'gzip, deflate', 'accept-language': 'en-US,en;q=0.9,fr;q=0.5'},
    {'upgrade-insecure-requests': '1', 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/73.0.3683.75 Safari/537.36', 'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8', 'sec-ch-ua': 'Google Chrome;v="73", "Chromium";v="73", ";Not A Brand";v="99"', 'sec-ch-ua-mobile': '?0', 'sec-ch-ua-platform': 'Windows', 'sec-fetch-site': 'none', 'sec-fetch-mod': '', 'sec-fetch-user': '?1', 'accept-encoding': 'gzip, deflate', 'accept-language': 'en-US,es;q=0.8'},
    {'upgrade-insecure-requests': '1', 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.85 Safari/537.36 Edg/90.0.818.49', 'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8', 'sec-ch-ua': 'Microsoft Edge;v="90", "Chromium";v="90", ";Not A Brand";v="99"', 'sec-ch-ua-mobile': '?0', 'sec-ch-ua-platform': 'Windows', 'sec-fetch-site': 'none', 'sec-fetch-mod': '', 'sec-fetch-user': '?1', 'accept-encoding': 'gzip, deflate', 'accept-language': 'en-US,it;q=0.9'},
    {'upgrade-insecure-requests': '1', 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.114 Safari/537.36 Edg/89.0.774.68', 'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8', 'sec-ch-ua': 'Microsoft Edge;v="89", "Chromium";v="89", ";Not A Brand";v="99"', 'sec-ch-ua-mobile': '?0', 'sec-ch-ua-platform': 'Windows', 'sec-fetch-site': 'none', 'sec-fetch-mod': '', 'sec-fetch-user': '?1', 'accept-encoding': 'gzip, deflate', 'accept-language': 'en-US,it;q=0.9'},
    {'upgrade-insecure-requests': '1', 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.198 Safari/537.36 Edg/86.0.622.69', 'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8', 'sec-ch-ua': 'Microsoft Edge;v="86", "Chromium";v="86", ";Not A Brand";v="99"', 'sec-ch-ua-mobile': '?0', 'sec-ch-ua-platform': 'Windows', 'sec-fetch-site': 'none', 'sec-fetch-mod': '', 'sec-fetch-user': '?1', 'accept-encoding': 'gzip', 'accept-language': 'en-US,fr;q=0.5'},
    {'upgrade-insecure-requests': '1', 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.135 Safari/537.36 Edg/84.0.522.63', 'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3', 'sec-ch-ua': 'Microsoft Edge;v="84", "Chromium";v="84", ";Not A Brand";v="99"', 'sec-ch-ua-mobile': '?0', 'sec-ch-ua-platform': 'Windows', 'sec-fetch-site': 'none', 'sec-fetch-mod': '', 'sec-fetch-user': '?1', 'accept-encoding': 'gzip, deflate', 'accept-language': 'en-US,fr;q=0.8'},
    {'upgrade-insecure-requests': '1', 'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/72.0.3626.121 Safari/537.36', 'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8', 'sec-ch-ua': 'Google Chrome;v="72", "Chromium";v="72", ";Not A Brand";v="99"', 'sec-ch-ua-mobile': '?0', 'sec-ch-ua-platform': 'Windows', 'sec-fetch-site': 'none', 'sec-fetch-mod': '', 'sec-fetch-user': '?1', 'accept-encoding': 'gzip, deflate', 'accept-language': 'en-US,it;q=0.7'},
    {'upgrade-insecure-requests': '1', 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/81.0.4044.138 Safari/537.36', 'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8', 'sec-ch-ua': 'Google Chrome;v="81", "Chromium";v="81", ";Not A Brand";v="99"', 'sec-ch-ua-mobile': '?0', 'sec-ch-ua-platform': 'Windows', 'sec-fetch-site': 'none', 'sec-fetch-mod': '', 'sec-fetch-user': '?1', 'accept-encoding': 'gzip', 'accept-language': 'en-US,en;q=0.7'},
]


def lru_cache_freezeargs(func):
    """
    Decorator transforms mutable dictionary and list arguments into immutable types
    Needed so lru_cache can cache method calls what has dict or list arguments.
    """

    @functools.wraps(func)
    def wrapped(*args, **kwargs):
        args = tuple([frozendict(arg) if isinstance(arg, dict) else arg for arg in args])
        kwargs = {k: frozendict(v) if isinstance(v, dict) else v for k, v in kwargs.items()}
        args = tuple([tuple(arg) if isinstance(arg, list) else arg for arg in args])
        kwargs = {k: tuple(v) if isinstance(v, list) else v for k, v in kwargs.items()}
        return func(*args, **kwargs)
    # copy over the lru_cache extra methods to this wrapper to be able to access them
    # after this decorator has been applied
    wrapped.cache_info = func.cache_info
    wrapped.cache_clear = func.cache_clear
    return wrapped


class SingletonMeta(type):
    """
    Metaclass that creates a Singleton instance.
    """
    _instances = {}
    _lock = threading.Lock()

    def __call__(cls, *args, **kwargs):
        with cls._lock:
            if cls not in cls._instances:
                instance = super().__call__(*args, **kwargs)
                cls._instances[cls] = instance
            else:
                cls._instances[cls]._set_session(*args, **kwargs)
            return cls._instances[cls]


class SessionManager(metaclass=SingletonMeta):
    """
    Have one place to retrieve data from Yahoo API in order to ease caching and speed up operations.
    Singleton means one session one cookie shared by all threads.
    """
    user_agent_headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'
    }

    def __init__(self, session=None):
        self._session = session or requests.Session()
        try:
            self._session.cache
        except AttributeError:
            # Not caching
            self._session_is_caching = False
        else:
            # Is caching. This is annoying.
            # Can't simply use a non-caching session to fetch cookie & crumb,
            # because then the caching-session won't have cookie.
            self._session_is_caching = True
            from requests_cache import DO_NOT_CACHE
            self._expire_after = DO_NOT_CACHE
        self._crumb = None
        self._cookie = None
        if self._session_is_caching and self._cookie is None:
            logging.warning(
                "yahoofinancials: cookie & crumb does not work well with requests_cache. Am experimenting with "
                "'expire_after=DO_NOT_CACHE', but you need to help stress-test."
            )
        # Default to using 'basic' strategy
        self._cookie_strategy = 'basic'
        # If it fails, then fallback method is 'csrf'
        # self._cookie_strategy = 'csrf'
        self._cookie_lock = threading.Lock()

    def _set_session(self, session):
        if session is None:
            return
        with self._cookie_lock:
            self._session = session

    def _set_cookie_strategy(self, strategy, have_lock=False):
        if strategy == self._cookie_strategy:
            return
        if not have_lock:
            self._cookie_lock.acquire()

        try:
            if self._cookie_strategy == 'csrf':
                logging.info(f'yahoofinancials: toggling cookie strategy {self._cookie_strategy} -> basic')
                self._session.cookies.clear()
                self._cookie_strategy = 'basic'
            else:
                logging.info(f'yahoofinancials: toggling cookie strategy {self._cookie_strategy} -> csrf')
                self._cookie_strategy = 'csrf'
            self._cookie = None
            self._crumb = None
        except Exception:
            self._cookie_lock.release()
            raise

        if not have_lock:
            self._cookie_lock.release()

    def _save_session_cookies(self):
        try:
            cache.get_cookie_cache().store('csrf', self._session.cookies)
        except Exception:
            return False
        return True

    def _load_session_cookies(self):
        cookie_dict = cache.get_cookie_cache().lookup('csrf')
        if cookie_dict is None:
            return False
        # Periodically refresh, 24 hours seems fair.
        if cookie_dict['age'] > datetime.timedelta(days=1):
            return False
        self._session.cookies.update(cookie_dict['cookie'])
        logging.info('yahoofinancials: loaded persistent cookie')

    def _save_cookie_basic(self, cookie):
        try:
            cache.get_cookie_cache().store('basic', cookie)
        except Exception:
            return False
        return True

    def _load_cookie_basic(self):
        cookie_dict = cache.get_cookie_cache().lookup('basic')
        if cookie_dict is None:
            return None
        # Periodically refresh, 24 hours seems fair.
        if cookie_dict['age'] > datetime.timedelta(days=1):
            return None
        logging.info('yahoofinancials: loaded persistent cookie')
        return cookie_dict['cookie']

    def _get_cookie_basic(self, proxy=None, timeout=30):
        if self._cookie is not None:
            logging.info('yahoofinancials: reusing cookie')
            return self._cookie

        self._cookie = self._load_cookie_basic()
        if self._cookie is not None:
            return self._cookie

        # To avoid infinite recursion, do NOT use self.get()
        # - 'allow_redirects' copied from @psychoz971 solution - does it help USA?
        response = self._session.get(
            url='https://finance.yahoo.com',
            headers=self.user_agent_headers,
            proxies=proxy,
            timeout=timeout,
            allow_redirects=True)

        if not response.cookies:
            logging.info("yahoofinancials: response.cookies = None")
            return None
        self._cookie = list(response.cookies)[0]
        if self._cookie == '':
            logging.info("yahoofinancials: list(response.cookies)[0] = ''")
            return None
        self._save_cookie_basic(self._cookie)
        logging.info(f"yahoofinancials: fetched basic cookie = {self._cookie}")
        return self._cookie

    def _get_crumb_basic(self, proxy=None, timeout=30):
        if self._crumb is not None:
            logging.info('yahoofinancials: reusing crumb')
            return self._crumb

        cookie = self._get_cookie_basic()
        if cookie is None:
            return None

        # - 'allow_redirects' copied from @psychoz971 solution - does it help USA?
        get_args = {
            'url': "https://query1.finance.yahoo.com/v1/test/getcrumb",
            'headers': self.user_agent_headers,
            'cookies': {cookie.name: cookie.value},
            'proxies': proxy,
            'timeout': timeout,
            'allow_redirects': True
        }
        if self._session_is_caching:
            get_args['expire_after'] = self._expire_after
            crumb_response = self._session.get(**get_args)
        else:
            crumb_response = self._session.get(**get_args)
        self._crumb = crumb_response.text
        if self._crumb is None or '<html>' in self._crumb:
            logging.info("yahoofinancials: didn't receive crumb")
            return None

        logging.info(f"yahoofinancials: crumb = '{self._crumb}'")
        return self._crumb

    def _get_cookie_and_crumb_basic(self, proxy, timeout):
        cookie = self._get_cookie_basic(proxy, timeout)
        crumb = self._get_crumb_basic(proxy, timeout)
        return cookie, crumb

    def _get_cookie_csrf(self, proxy, timeout):
        if self._cookie is not None:
            logging.info('yahoofinancials: reusing cookie')
            return True

        elif self._load_session_cookies():
            logging.info('yahoofinancials: reusing persistent cookie')
            self._cookie = True
            return True

        base_args = {
            'headers': self.user_agent_headers,
            'proxies': proxy,
            'timeout': timeout}

        get_args = {**base_args, 'url': 'https://guce.yahoo.com/consent'}
        if self._session_is_caching:
            get_args['expire_after'] = self._expire_after
            response = self._session.get(**get_args)
        else:
            response = self._session.get(**get_args)

        soup = BeautifulSoup(response.content, 'html.parser')
        csrfTokenInput = soup.find('input', attrs={'name': 'csrfToken'})
        if csrfTokenInput is None:
            logging.info('yahoofinancials: Failed to find "csrfToken" in response')
            return False
        csrfToken = csrfTokenInput['value']
        logging.info(f'csrfToken = {csrfToken}')
        sessionIdInput = soup.find('input', attrs={'name': 'sessionId'})
        sessionId = sessionIdInput['value']
        logging.info(f"sessionId='{sessionId}")

        originalDoneUrl = 'https://finance.yahoo.com/'
        namespace = 'yahoo'
        data = {
            'agree': ['agree', 'agree'],
            'consentUUID': 'default',
            'sessionId': sessionId,
            'csrfToken': csrfToken,
            'originalDoneUrl': originalDoneUrl,
            'namespace': namespace,
        }
        post_args = {**base_args,
                     'url': f'https://consent.yahoo.com/v2/collectConsent?sessionId={sessionId}',
                     'data': data}
        get_args = {**base_args,
                    'url': f'https://guce.yahoo.com/copyConsent?sessionId={sessionId}',
                    'data': data}
        if self._session_is_caching:
            post_args['expire_after'] = self._expire_after
            get_args['expire_after'] = self._expire_after
            self._session.post(**post_args)
            self._session.get(**get_args)
        else:
            self._session.post(**post_args)
            self._session.get(**get_args)
        self._cookie = True
        self._save_session_cookies()
        return True

    def _get_crumb_csrf(self, proxy=None, timeout=30):
        if self._crumb is not None:
            logging.info('yahoofinancials: reusing crumb')
            return self._crumb
        if not self._get_cookie_csrf(proxy, timeout):
            # This cookie stored in session
            return None
        get_args = {
            'url': 'https://query2.finance.yahoo.com/v1/test/getcrumb',
            'headers': self.user_agent_headers,
            'proxies': proxy,
            'timeout': timeout}
        if self._session_is_caching:
            get_args['expire_after'] = self._expire_after
            r = self._session.get(**get_args)
        else:
            r = self._session.get(**get_args)
        self._crumb = r.text
        if self._crumb is None or '<html>' in self._crumb or self._crumb == '':
            logging.info("yahoofinancials: didn't receive crumb")
            return None
        logging.info(f"yahoofinancials: crumb = '{self._crumb}'")
        return self._crumb

    def _get_cookie_and_crumb(self, proxy=None, timeout=30):
        cookie, crumb, strategy = None, None, None
        logging.info(f"yahoofinancials: cookie_mode = '{self._cookie_strategy}'")
        with self._cookie_lock:
            if self._cookie_strategy == 'csrf':
                crumb = self._get_crumb_csrf()
                if crumb is None:
                    # Fail
                    self._set_cookie_strategy('basic', have_lock=True)
                    cookie, crumb = self._get_cookie_and_crumb_basic(proxy, timeout)
            else:
                # Fallback strategy
                cookie, crumb = self._get_cookie_and_crumb_basic(proxy, timeout)
                if cookie is None or crumb is None:
                    # Fail
                    self._set_cookie_strategy('csrf', have_lock=True)
                    crumb = self._get_crumb_csrf()
            strategy = self._cookie_strategy
        return cookie, crumb, strategy

    def get(self, url, user_agent_headers=None, params=None, proxy=None, timeout=30):
        # Important: treat input arguments as immutable.
        proxy = self._get_proxy(proxy)
        if params is None:
            params = {}
        if 'crumb' in params:
            raise Exception("yahoofinancials: Don't manually add 'crumb' to params dict, let sessions.py handle it")
        cookie, crumb, strategy = self._get_cookie_and_crumb()
        if crumb is not None:
            crumbs = {'crumb': crumb}
        else:
            crumbs = {}
        if strategy == 'basic' and cookie is not None:
            # Basic cookie strategy adds cookie to GET parameters
            cookies = {cookie.name: cookie.value}
        else:
            cookies = None
        request_args = {
            'url': url,
            'params': {**params, **crumbs},
            'cookies': cookies,
            'proxies': proxy,
            'timeout': timeout,
            'headers': user_agent_headers or self.user_agent_headers
        }
        response = self._session.get(**request_args)
        if response.status_code >= 400:
            # Retry with other cookie strategy
            if strategy == 'basic':
                self._set_cookie_strategy('csrf')
            else:
                self._set_cookie_strategy('basic')
            cookie, crumb, strategy = self._get_cookie_and_crumb(proxy, timeout)
            request_args['params']['crumb'] = crumb
            if strategy == 'basic':
                request_args['cookies'] = {cookie.name: cookie.value}
            response = self._session.get(**request_args)

        return response

    @lru_cache_freezeargs
    @lru_cache(maxsize=cache_maxsize)
    def cache_get(self, url, user_agent_headers=None, params=None, proxy=None, timeout=30):
        return self.get(url, user_agent_headers, params, proxy, timeout)

    def _get_proxy(self, proxy):
        # setup proxy in requests format
        if proxy is not None:
            if isinstance(proxy, (dict, frozendict)) and "https" in proxy:
                proxy = proxy["https"]
            proxy = {"https": proxy}
        return proxy

    def get_raw_json(self, url, user_agent_headers=None, params=None, proxy=None, timeout=30):
        logging.info(f'yahoofinancials: get_raw_json(): {url}')
        response = self.get(url, user_agent_headers=user_agent_headers, params=params, proxy=proxy, timeout=timeout)
        response.raise_for_status()
        return response.json()


class TimeoutHTTPAdapter(HTTPAdapter):
    def __init__(self, *args, **kwargs):
        self.timeout = DEFAULT_TIMEOUT
        if "timeout" in kwargs:
            self.timeout = kwargs["timeout"]
            del kwargs["timeout"]
        super(TimeoutHTTPAdapter, self).__init__(*args, **kwargs)

    def send(self, request, **kwargs):
        timeout = kwargs.get("timeout")
        if timeout is None:
            kwargs["timeout"] = self.timeout
        return super(TimeoutHTTPAdapter, self).send(request, **kwargs)


def setup_session_with_cookies_and_crumb(session: Session):
    headers = {**random.choice(HEADERS)}
    session.headers = headers
    try:
        response = session.get('https://finance.yahoo.com')
    except Exception:
        return session, None
    else:
        session.cookies = response.cookies
        crumb = _get_crumb(session)
        return session, crumb


def _get_crumb(session):
    try:
        response = session.get('https://query2.finance.yahoo.com/v1/test/getcrumb')
        return response.text
    except (ConnectionError, RetryError) as e:
        # Cookies most likely not set in previous request
        return None


def _init_session(session=None, **kwargs):
    crumb = None
    if session is None:
        session = Session()
        if kwargs.get("proxies"):
            session.proxies = kwargs.get("proxies")
        retries = Retry(
            total=kwargs.get("retry", 5),
            backoff_factor=kwargs.get("backoff_factor", 0.3),
            status_forcelist=kwargs.get("status_forcelist", [429, 500, 502, 503, 504]),
        )
        if kwargs.get("verify") is not None:
            session.verify = kwargs.get("verify")
        session.mount(
            "https://",
            TimeoutHTTPAdapter(
                max_retries=retries, timeout=kwargs.get("timeout", DEFAULT_TIMEOUT)
            ),
        )
        session, crumb = setup_session_with_cookies_and_crumb(session)
    return session, crumb
