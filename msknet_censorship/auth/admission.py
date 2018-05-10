from msknet_censorship.utils import group_api
from django.contrib.auth.models import Group

def save_group_permission(backend, user, response, *args, **kwargs):
    if backend.name == 'discourse':
        duid = int(response['external_id'])
        admission = Group.objects.get_or_create(name='admission')[0]
        if group_api.is_censor(duid):
            user.groups.add(admission)
        else:
            user.groups.remove(admission)
        user.save()