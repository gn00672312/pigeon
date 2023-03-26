# -*- coding: utf-8 -*-
import re
import datetime
import uuid

FORMAT = 'format'
YMDHMS = '%Y%m%d%H%M%S'
TIMESTAMP_UTC = re.compile(r'\{timestamp_utc(\|(?P<format>[^ }]+))*}')
TIMESTAMP_LST = re.compile(r'\{timestamp_lst(\|(?P<format>[^ }]+))*}')

TAG_UUID = re.compile(r'\{uuid}')
TAG_SOURCE_NAME = re.compile(r'\{source_name}')
TAG_INIT_TIME = re.compile(r'\{init_time(\|(?P<format>[^ }]+))*}')
TAG_MEMBER_NO = re.compile(r'\{member_no}')
TAG_TAU_MAX = re.compile(r'\{tau_max}')
TAG_TAU_RESOLUTION = re.compile(r'\{tau_resolution}')
TAG_PARAM = re.compile(r'\{param}')


def translate_tags(tag, source_name=None, init_time=None, member_no=None,
        tau_max=None, tau_resolution=None, param=None):
    """
    Parse the given name and translate all tags begin by '{' and end by '}'.
    Currently we support the following tag translation:
    """
    result = tag
    if source_name is not None:
        result = re.sub(TAG_SOURCE_NAME, source_name, result)
    if init_time is not None:
        result = trans_init(init_time, result)
    if member_no is not None:
        result = re.sub(TAG_MEMBER_NO, member_no, result)
    if tau_max is not None:
        result = re.sub(TAG_TAU_MAX, tau_max, result)
    if tau_resolution is not None:
        result = re.sub(TAG_TAU_RESOLUTION, tau_resolution, result)
    if param is not None:
        result = re.sub(TAG_PARAM, param, result)

    result = re.sub(TAG_UUID, str(uuid.uuid1()), result)
    result = trans_timestamp(result)

    return result


def trans_init(init_time, string):
    """
     -- {init_time|format}
        Here the 'format' uses datetime.strftime specs and extend
        '%3f' to be the millisecond. If 'format' is omitted, uses
        '%Y-%m-%d %H:%M:%S' as default. Also the '|' sign can't appear
        there in such case.
    """
    mo = TAG_INIT_TIME.search(string)
    if mo:
        dtime_format = mo.groupdict().get(FORMAT) or YMDHMS
        timestamp = strftime(init_time, dtime_format)
        string = re.sub(TAG_INIT_TIME, timestamp, string)
    return string


def trans_timestamp(string):
    """
     -- {timestamp_lst|format}
     -- {timestamp_utc|format}
        Here the 'format' uses datetime.strftime specs and extend
        '%3f' to be the millisecond. If 'format' is omitted, uses
        '%Y-%m-%d %H:%M:%S' as default. Also the '|' sign can't appear
        there in such case.
    """
    timestamp_lst = datetime.datetime.now()
    timestamp_utc = timestamp_lst - datetime.timedelta(hours=8)
    mo = TIMESTAMP_UTC.search(string)
    if mo:
        dtime_format = mo.groupdict().get(FORMAT) or YMDHMS
        timestamp = strftime(timestamp_utc, dtime_format)
        string = re.sub(TIMESTAMP_UTC, timestamp, string)
    mo = TIMESTAMP_LST.search(string)
    if mo:
        dtime_format = mo.groupdict().get(FORMAT) or YMDHMS
        timestamp = strftime(timestamp_lst, dtime_format)
        string = re.sub(TIMESTAMP_LST, timestamp, string)
    return string


def strftime(dtime, dtime_format):
    """
    Custom, extended, version for the datetime.strftime() to has the
    following capabilities:

     -- %3f
        Millisecond as a decimal number [0, 999], zero-padded on the left.
     -- %-3f
        Millisecond as a decimal number [0, 999], no zero-padded on the
        left.
    """
    assert isinstance(dtime, (datetime.date, datetime.time,
                              datetime.datetime))

    result = ''
    num_ignore = 0
    last = len(dtime_format) - 1
    for i, s in enumerate(dtime_format):
        if num_ignore > 0:
            num_ignore -= 1
            continue
        if s == '%' and i != last:
            if dtime_format[i + 1] == '%':
                num_ignore = 1
                result += '%%'
            elif dtime_format[i + 1: i + 3] == '3f':
                num_ignore = 2
                result += dtime.strftime('%f')[:3]
            elif dtime_format[i + 1: i + 4] == '-3f':
                num_ignore = 3
                result += str(getattr(dtime, 'microsecond', 0))
            else:
                num_ignore = 0
                result += s
        else:
            result += s
    return dtime.strftime(result)
