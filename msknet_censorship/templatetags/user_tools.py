from django import template
import hashlib
import time

register = template.Library()

def hide_username(value):
    m = hashlib.sha256()
    m.update(b'%b%d' % (str(value).encode(), time.time()))
    return m.hexdigest()[0:16]

register.filter('hide_username', hide_username)