from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.core.cache import cache
from django.core.mail import send_mail
from django.conf import settings
from .models import Product, Order
import logging

logger = logging.getLogger(__name__)

@receiver([post_save, post_delete], sender=Product)
def clear_product_cache(sender, instance, **kwargs):
    cache.delete("product_list")
    cache.delete(f"product_detail_{instance.id}")
    print(f"Cache cleared for Product {instance.id}")

@receiver(post_save, sender=Order)
def send_order_confirmation(sender, instance, created, **kwargs):
    """
    Sends an email confirmation when an order status changes to 'processing'
    (which happens after successful payment).
    """
    # Check if the status was just changed to processing
    # Note: In a real app, we might want to track the previous status to avoid duplicate emails
    # But for this simulation, checking for 'processing' status is a good trigger point.
    if instance.status == "processing" and instance.user.email:
        try:
            subject = f"Order Confirmation - #{instance.id}"
            message = f"Hi {instance.user.username},\n\n" \
                      f"Thank you for your order! Your payment was successful.\n\n" \
                      f"Order ID: #{instance.id}\n" \
                      f"Total Amount: ${instance.final_price:,.2f} USD\n" \
                      f"Shipping to: {instance.shipping_address}, {instance.shipping_city}\n\n" \
                      f"We will notify you once your order has been shipped.\n\n" \
                      f"Best regards,\nEcommerce Team"
            
            recipient_list = [instance.user.email]
            
            if settings.EMAIL_HOST_USER:
                send_mail(
                    subject,
                    message,
                    settings.DEFAULT_FROM_EMAIL,
                    recipient_list,
                    fail_silently=False,
                )
                print(f"Order confirmation email sent to {instance.user.email} for Order #{instance.id}")
            else:
                print(f"Skipping email for Order #{instance.id}: EMAIL_HOST_USER not configured in .env")
                
        except Exception as e:
            logger.error(f"Failed to send order confirmation email: {str(e)}")
            print(f"Error sending email: {str(e)}")
