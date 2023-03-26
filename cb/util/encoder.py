from datetime import datetime
from decimal import Decimal

from django.core.serializers.json import DjangoJSONEncoder


class PrettyFloat(float):
    def __repr__(self):
        return '%.15g' % self


class JSONEncoder(DjangoJSONEncoder):

    def default_key(self, obj):
        if isinstance(obj, float):
            return str(PrettyFloat(obj))
        if isinstance(obj, int):
            return str(obj)
        if isinstance(obj, Decimal):
            return str(obj)
        if isinstance(obj, (list, tuple)):
            return ','.join([self.default_key(item) for item in obj])
        return self.default(obj)

    def default(self, obj):
        if isinstance(obj, (list, tuple)):
            return map(self.default, obj)
        if isinstance(obj, datetime):
            return obj.strftime("%Y%m%d%H%M")
        if isinstance(obj, Decimal):
            return PrettyFloat(float(obj))
        if isinstance(obj, float):
            return PrettyFloat(obj)
        return super(JSONEncoder, self).default(obj)
