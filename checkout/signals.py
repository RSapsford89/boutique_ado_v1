from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

from .models import OrderLineItem


@receiver(post_save, sender=OrderLineItem)
def update_on_save(sender, instance, created, **kwargs):
    """
    update order total on lineitem update/create
    where: sender of signal, instance of sending model
    bool of if created or update 
    """
    instance.order.update_total()

@receiver(post_delete, sender=OrderLineItem)
def update_on_delete(sender, instance,  **kwargs):
    """
    update order total on lineitem delete
    where: sender of signal, instance of sending model
    bool if created or update 
    """
    instance.order.update_total()