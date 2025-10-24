from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from apps.customers import models


@receiver(post_delete, sender=models.Account)
def remove_account_user(sender, instance, **kwargs):
    """Delete the associated user when an account is deleted."""
    user = instance.user
    user.delete()


@receiver(post_save, sender=models.Company)
def create_principal_branch(sender, instance, created, **kwargs):
    """
    Automatically create a 'Principal' branch when a new Company is created.

    Args:
        sender: The model class (Company).
        instance: The actual instance being saved.
        created: Boolean indicating if this is a new instance.
        **kwargs: Additional keyword arguments.
    """
    if created:
        models.Branch.objects.create(
            company=instance,
            name="Principal",
            sunat_code="0000",
            description="Sucursal principal",
            address=instance.address,
            country=instance.country,
            region=instance.region,
            subregion=instance.subregion,
            city=instance.city,
            phone=instance.phone,
            email=instance.email,
        )
