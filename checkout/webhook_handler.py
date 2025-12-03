from django.http import HttpResponse
from .models import Order, OrderLineItem
from products.models import Product
import json
import time
import stripe
from django.conf import settings


class StripeWH_Handler:
    """
    Handle Stripe  Webhooks
    """

    def __init__(self, request):
        self.request = request

    def handle_event(self, event):
        """
        handle a generic/unknown/unexpected webhook event
        """
        return HttpResponse(
            content=f"Unhandled Webhook received: {event['type']}",
            status=200
        )

    def handle_payment_intent_succeeded(self, event):
        """
        handle a payment_intent.succeeded webhook from stripe
        """
        intent = event.data.object
        
        # DEBUG: Print full intent object
        print('Intent:', intent)
        
        pid = intent.id

        # for testing...
        time.sleep(3)

        bag = intent.metadata.bag
        save_info = intent.metadata.save_info
        email = intent.metadata.get('email', '')  # Get email from metadata with fallback
        
        # DEBUG: Print extracted metadata
        print('PID:', pid)
        print('Bag:', bag)
        print('Save Info:', save_info)
        print('Email:', email)

        # Get billing/shipping from PaymentIntent
        stripe.api_key = settings.STRIPE_SECRET_KEY

        # Retrieve the charge to get billing details (optional now)
        billing_details = None
        if intent.latest_charge:
            try:
                charge = stripe.Charge.retrieve(intent.latest_charge)
                billing_details = charge.billing_details
                print('Billing Details:', billing_details)
            except Exception as e:
                print('Error retrieving charge:', e)
                pass

        shipping_details = intent.shipping
        
        # DEBUG: Print shipping details
        print('Shipping Details:', shipping_details)
        
        # Validate shipping details exist
        if not shipping_details:
            print('ERROR: No shipping details provided')
            return HttpResponse(
                content=f"Webhook received: {event['type']} | ERROR: No shipping details",
                status=400
            )
            
        grand_total = round(intent.amount / 100, 2)
        
        print('Grand Total:', grand_total)

        # Clean data in the shipping details
        for field, value in shipping_details.address.items():
            if value == "":
                shipping_details.address[field] = None

        # Check if order exists
        order_exists = False
        attempt = 1
        while attempt <= 5:
            try:
                print(f'Attempting to find order (attempt {attempt}/5)...')
                order = Order.objects.get(
                    full_name__iexact=shipping_details.name,
                    email__iexact=email,  # Use metadata email
                    phone_number__iexact=shipping_details.phone,
                    country__iexact=shipping_details.address.country,
                    postcode__iexact=shipping_details.address.postal_code,
                    town_or_city__iexact=shipping_details.address.city,
                    street_address1__iexact=shipping_details.address.line1,
                    street_address2__iexact=shipping_details.address.line2,
                    county__iexact=shipping_details.address.state,
                    grand_total=grand_total,
                    original_bag=bag,
                    stripe_pid=pid,
                )
                order_exists = True
                print(f'Order found: {order.order_number}')
                break
            except Order.DoesNotExist:
                print(f'Order not found, attempt {attempt}/5')
                attempt += 1
                time.sleep(1)

        if order_exists:
            print('Returning 200 response - order already exists')
            return HttpResponse(
                content=f"Webhook received: {event['type']} | SUCCESS: Verified order already in database",
                status=200
            )
        else:
            print('Order not found after 5 attempts, creating from webhook...')
            order = None
            try:
                order = Order.objects.create(
                    full_name=shipping_details.name,
                    email=email,  # Use metadata email
                    phone_number=shipping_details.phone,
                    country=shipping_details.address.country,
                    postcode=shipping_details.address.postal_code,
                    town_or_city=shipping_details.address.city,
                    street_address1=shipping_details.address.line1,
                    street_address2=shipping_details.address.line2,
                    county=shipping_details.address.state,
                    original_bag=bag,
                    stripe_pid=pid,
                )
                print(f'Order created: {order.order_number}')
                
                for item_id, item_data in json.loads(bag).items():
                    product = Product.objects.get(id=item_id)
                    if isinstance(item_data, int):
                        order_line_item = OrderLineItem(
                            order=order,
                            product=product,
                            quantity=item_data,
                        )
                        order_line_item.save()
                        print(f'Created line item: {product.name} x {item_data}')
                    else:
                        for size, quantity in item_data['items_by_size'].items():
                            order_line_item = OrderLineItem(
                                order=order,
                                product=product,
                                quantity=quantity,
                                product_size=size,
                            )
                            order_line_item.save()
                            print(f'Created line item: {product.name} (size {size}) x {quantity}')
            except Exception as e:
                if order:
                    order.delete()
                print(f'ERROR creating order: {e}')
                return HttpResponse(
                    content=f"Webhook received: {event['type']} | ERROR: {e}",
                    status=500
                )

        print('Returning 200 response - order created successfully')
        return HttpResponse(
            content=f"Webhook received: {event['type']} | SUCCESS: Created order in webhook",
            status=200
        )

    def handle_payment_intent_failed(self, event):
        """
        handle a payment_intent.payment_failed webhook from stripe
        """
        intent = event.data.object
        print('Payment failed for intent:', intent.id)
        return HttpResponse(
            content=f"Webhook received: {event['type']}",
            status=200
        )