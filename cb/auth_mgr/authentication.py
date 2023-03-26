import requests
import multiprocessing
from datetime import datetime

from rest_framework.authentication import BaseAuthentication, get_authorization_header
from rest_framework.exceptions import AuthenticationFailed

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.exceptions import MultipleObjectsReturned
from django.utils.translation import ugettext_lazy as _

from module import log

User = get_user_model()

if not getattr(settings, 'REMOTE_AUTH', None):
    raise AttributeError('Must set REMOTE_AUTH to settings.')


class RemoteAuthentication(BaseAuthentication):
    keyword = 'Token'

    def authenticate(self, request):
        user = None
        token = None

        # 這裡是從原來的 TokenAuthentication 抄來的，主要是檢查 token 的格式
        auth = get_authorization_header(request).split()

        if not auth or auth[0].lower() != self.keyword.lower().encode():
            return None

        if len(auth) == 1:
            msg = _('Invalid token header. No credentials provided.')
            raise AuthenticationFailed(msg)
        elif len(auth) > 2:
            msg = _('Invalid token header. Token string should not contain spaces.')
            raise AuthenticationFailed(msg)

        try:
            token = auth[1].decode()
        except UnicodeError:
            msg = _('Invalid token header. Token string should not contain invalid characters.')
            raise AuthenticationFailed(msg)

        response = authenticate({'token': token})
        if response:
            try:
                user, created = User.objects.get_or_create(username=response['username'])
                if created:
                    log.event(f'User {user.username} is not exist in local, create a new one...')
                else:
                    log.event(f'User {user.username} already exists in local, wont\'t be created.')
            except MultipleObjectsReturned:
                log.event(f'Multiple {user.username} users.')
                raise AuthenticationFailed('Multiple users.')
            return (user, token)

        # 從 remote 都找不到這個 user ， return None(not return (None, None)) 讓下一個 Authtication Class 可以 handle
        return None


def authenticate(data, auth_settings=settings.REMOTE_AUTH):
    start = datetime.now()

    remote_hosts = auth_settings.get('HOSTS_URL')
    timeout = auth_settings.get('TIMEOUT')

    processs = []
    result_queue = multiprocessing.Queue()

    for host in remote_hosts:
        process = multiprocessing.Process(target=authenticate_request, args=[result_queue, host, data, timeout])
        process.start()
        processs.append(process)

    result = {}
    try:
        # 至少要從 queue 取得相對應 remote_hosts 數量的 response
        for host in remote_hosts:
            # queue.get 會 block 住，直到 timeout(raise Empty exception) 或是真的有東西進入 queue
            result = result_queue.get(timeout=timeout)
            if result.get('id') or result.get('username'):
                break
        else:
            log.event('All authentication requests to remote_hosts failed.')

    except multiprocessing.queues.Empty:
        log.event('All authentication requests to remote_hosts failed.')

    # 只要有資料回來，process 要記得關掉
    for process in processs:
        process.terminate()

    log.debug(f'Authentication take {datetime.now() - start} time.')
    return result


def authenticate_request(result_queue, url, data, timeout):
    try:
        res = requests.post(url, data, timeout=timeout)
        result = res.json()
        if result:
            log.event(f'The User from remote <{url}> is <username: {result["username"]} id: {result["id"]}>.')
        else:
            log.event(f'The Token does not exist in remote <{url}>. Response from remote is: {result}.')
        result_queue.put(result)
    except requests.exceptions.ReadTimeout:
        log.event(f'Authenticate to Server({url}) timeout.')
