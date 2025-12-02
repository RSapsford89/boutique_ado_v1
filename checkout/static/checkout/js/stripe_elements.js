/*
    Core logic/payment flow for this comes from here:
    https://stripe.com/docs/payments/accept-a-payment
    
    Using Stripe Payment Element:
    https://stripe.com/docs/payments/payment-element
*/

var stripePublicKey = $('#id_stripe_public_key').text().slice(1, -1);
var clientSecret = $('#id_client_secret').text().slice(1, -1);
var stripe = Stripe(stripePublicKey);

// Initialize Elements with clientSecret
const elements = stripe.elements({
    clientSecret: clientSecret,
    appearance: {
        theme: 'stripe',
        variables: {
            colorPrimary: '#000000',
            colorBackground: '#ffffff',
            colorText: '#000000',
            colorDanger: '#dc3545',
            fontFamily: '"Helvetica Neue", Helvetica, sans-serif',
            spacingUnit: '4px',
            borderRadius: '4px'
        }
    }
});

// Create and mount the Payment Element
const paymentElement = elements.create('payment', {
    layout: 'accordion'
});
paymentElement.mount('#payment-element');

// Handle realtime validation errors on the payment element
paymentElement.on('change', function(event) {
    var errorDiv = document.getElementById('card-errors');
    if (event.error) {
        var html = `
            <span class="icon" role="alert">
                <i class="fas fa-times"></i>
            </span>
            <span>${event.error.message}</span>
        `;
        $(errorDiv).html(html);
    } else {
        errorDiv.textContent = '';
    }
});

// Handle form submit
var form = document.getElementById('payment-form');

form.addEventListener('submit', async function(ev) {
    ev.preventDefault();
    
    // Disable form elements
    paymentElement.update({ readOnly: true });
    $('#submit-button').attr('disabled', true);
    
    // Get form data
    var saveInfo = Boolean($('#id-save-info').attr('checked'));
    var csrfToken = $('input[name="csrfmiddlewaretoken"]').val();
    var postData = {
        'csrfmiddlewaretoken': csrfToken,
        'client_secret': clientSecret,
        'save_info': saveInfo,
        'email': $.trim($('#id_email').val()),  // Changed from form.email.value
    };
    var url = '/checkout/cache_checkout_data/';
    
    // Cache checkout data before confirming payment
    $.post(url, postData).done(async function() {
        // Confirm the payment with shipping details
        const {error, paymentIntent} = await stripe.confirmPayment({
            elements,
            confirmParams: {
                // Remove return_url completely
                shipping: {
                    name: $.trim($('#id_full_name').val()),
                    phone: $.trim($('#id_phone_number').val()),
                    address: {
                        line1: $.trim($('#id_street_address1').val()),
                        line2: $.trim($('#id_street_address2').val()),
                        city: $.trim($('#id_town_or_city').val()),
                        state: $.trim($('#id_county').val()),
                        postal_code: $.trim($('#id_postcode').val()),
                        country: $.trim($('#id_country').val()),
                    }
                }
            },
            redirect: 'if_required'
        });
        
        if (error) {
            // Show error
            var errorDiv = document.getElementById('card-errors');
            var html = `
                <span class="icon" role="alert">
                    <i class="fas fa-times"></i>
                </span>
                <span>${error.message}</span>
            `;
            $(errorDiv).html(html);
            paymentElement.update({ readOnly: false });
            $('#submit-button').attr('disabled', false);
        } else if (paymentIntent && paymentIntent.status === 'succeeded') {
            // Add client_secret and submit form
            var hiddenInput = document.createElement('input');
            hiddenInput.setAttribute('type', 'hidden');
            hiddenInput.setAttribute('name', 'client_secret');
            hiddenInput.setAttribute('value', clientSecret);
            form.appendChild(hiddenInput);
            form.submit();
        }
    }).fail(function() {
        location.reload();
    });
});