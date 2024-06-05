import logging
from datetime import datetime, timedelta
from random import randint
from uuid import uuid4
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth import get_user_model
from django.db.models import CASCADE, CharField, DateTimeField, ForeignKey, Model, OneToOneField
from django.db.models.signals import post_save
from django.dispatch import receiver
try:
    from zoneinfo import ZoneInfo
except ImportError:
    from backports.zoneinfo import ZoneInfo


User = get_user_model()

class CatchpyProfile(Model):
    created = DateTimeField(auto_now_add=True, null=False)
    modified = DateTimeField(auto_now=True, null=False)
    user = OneToOneField(User, on_delete=CASCADE, related_name='catchpy_profile')
    prime_consumer = OneToOneField(
        'Consumer',
        related_name='prime_profile',
        null=True,
        on_delete=CASCADE)

    def __repr__(self):
        return self.user.username

    def __str__(self):
        return self.__repr__()


@receiver(post_save, sender=User)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    if created or not hasattr(instance, "catchpy_profile"):
        CatchpyProfile.objects.create(user=instance)
    instance.catchpy_profile.save()


def expire_in_weeks(ttl=24):
    return datetime.now(ZoneInfo('UTC')) + timedelta(weeks=ttl)


def generate_id():
    return str(uuid4())


class Consumer(Model):
    created = DateTimeField(auto_now_add=True, null=False)
    modified = DateTimeField(auto_now=True, null=False)
    consumer = CharField(max_length=128, primary_key=True, default=generate_id)
    secret_key = CharField(max_length=128, default=generate_id)
    expire_on = DateTimeField(default=expire_in_weeks)
    parent_profile = ForeignKey(
        'CatchpyProfile',
        related_name='consumers',
        null=True,
        on_delete=CASCADE)

    def has_expired(self, now=None):
        if now is None:
            now = datetime.now(ZoneInfo('UTC'))
        return self.expire_on < now

    def __repr__(self):
        return self.consumer

    def __str__(self):
        return self.__repr__()


@receiver(post_save, sender=CatchpyProfile)
def create_or_update_profile_consumer(sender, instance, created, **kwargs):
    if created:
        consumer = Consumer.objects.create(parent_profile=instance)
        instance.prime_consumer = consumer
        instance.save()
    else:
        if not hasattr(instance, 'prime_consumer') or instance.prime_consumer is None:
            consumer = Consumer.objects.create(parent_profile=instance)
            instance.prime_consumer = consumer
            instance.save()
        else:
            instance.prime_consumer.save()

