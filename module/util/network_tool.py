def get_client_ip(request):
    """
    to solve the issue
    Empty REMOTE_ADDR value in Django application when using nginx as
    reverse proxy in front of gunicorn

    another solution is write middleware
    https://stackoverflow.com/questions/34251298/empty-remote-addr-value-in-django-application-when-using-nginx-as-reverse-proxy
    :param request: request object
    :return: ip
    """
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip
