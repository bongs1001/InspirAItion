from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from django.db.utils import OperationalError
from .models import Profile


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        try:
            Profile.objects.create(
                user=instance, 
                nickname=instance.username,
                balance=10000
            )
        except OperationalError as e:
            import logging
            logging.error(f"Could not create user profile: {e}")


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, created, **kwargs):
    try:
        if hasattr(instance, "profile"):
            instance.profile.save()
    except Exception as e:
        import logging
        logging.error(f"Could not save user profile: {e}")