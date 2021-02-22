import logging
from datetime import datetime, timedelta
from random import randint
from uuid import uuid4

import pytz
from django.contrib.auth.models import User
from django.contrib.postgres.fields import JSONField
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import (
    CASCADE,
    PROTECT,
    BooleanField,
    CharField,
    DateTimeField,
    ForeignKey,
    ManyToManyField,
    Model,
    OneToOneField,
    TextField,
)
from django.db.models.signals import post_save
from django.dispatch import receiver


class Profile(Model):
    created = DateTimeField(auto_now_add=True, null=False)
    modified = DateTimeField(auto_now=True, null=False)
    user = OneToOneField(User, on_delete=CASCADE)
    prime_consumer = OneToOneField(
        "Consumer", related_name="prime_profile", null=True, on_delete=CASCADE
    )

    def __repr__(self):
        return self.user.username

    def __str__(self):
        return self.__repr__()


@receiver(post_save, sender=User)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)
    instance.profile.save()


def expire_in_weeks(ttl=24):
    return datetime.now(pytz.utc) + timedelta(weeks=ttl)


def generate_id():
    return str(uuid4())


class Consumer(Model):
    created = DateTimeField(auto_now_add=True, null=False)
    modified = DateTimeField(auto_now=True, null=False)
    consumer = CharField(max_length=128, primary_key=True, default=generate_id)
    secret_key = CharField(max_length=128, default=generate_id)
    expire_on = DateTimeField(default=expire_in_weeks)
    parent_profile = ForeignKey(
        "Profile", related_name="consumers", null=True, on_delete=CASCADE
    )

    def has_expired(self, now=None):
        if now is None:
            now = datetime.now(pytz.utc)
        return self.expire_on < now

    def __repr__(self):
        return self.consumer

    def __str__(self):
        return self.__repr__()


@receiver(post_save, sender=Profile)
def create_or_update_profile_consumer(sender, instance, created, **kwargs):
    if created:
        Consumer.objects.create(prime_profile=instance)
    instance.prime_consumer.save()
