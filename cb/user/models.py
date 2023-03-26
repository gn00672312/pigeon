# -*- coding: utf-8 -*-

from django.db import models
from django.utils.translation import ugettext_lazy as _


class Function(models.Model):
    """
    The functions system provides a way to assign functions
    to specific users and groups of users.
    """
    name = models.CharField(max_length=100, verbose_name=_('Function name'))
    code = models.CharField(max_length=100, unique=True,
                            verbose_name=_('Function code'))

    def __unicode__(self):
        return self.name

    class Meta:
        db_table = 'cb_function'
        ordering = ['code']

    def has_sub_function(self):
        return Function.objects.filter(code__startswith=self.code).count() > 1

    def structure(self, delimiter='_'):
        """
        Return string like xxx-xx-x where x is self name, xx is parent name,
        xxx is parent's parent name, like so on.

        If you want using this function in template, the delimiter must be
        the same as the default parameter since parameter providing is not
        permitted in template file.
        """
        tokens = self.code.split(delimiter)
        level = len(tokens) - 1
        result = ''

        if level == 1:
            result = self.name
        else:
            parent = Function.objects.get(code=delimiter.join(tokens[:-1]))
            result += parent.structure(delimiter) + '-' + self.name

        return result
