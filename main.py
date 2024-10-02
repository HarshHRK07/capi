from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

# Define URLs
PAYMENT_INTENT_URL = "https://api.stripe.com/v1/payment_intents"
THREEDS_AUTHENTICATE_URL = "https://api.stripe.com/v1/3ds2/authenticate"

# Define common headers
COMMON_HEADERS = {
    'User-Agent': "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML; like Gecko) Chrome/124.0.0.0 Mobile Safari/537.36",
    'Accept': "application/json",
    'Content-Type': "application/x-www-form-urlencoded",
    'origin': "https://js.stripe.com",
    'sec-fetch-site': "same-site",
    'sec-fetch-mode': "cors",
    'referer': "https://js.stripe.com/"
}

def confirm_payment_intent(client_secret, card_details, public_key, stripe_account=None, include_cvc=False):
    """
    Confirm the payment intent with the card details.
    """
    card_info = card_details.split('|')
    card_number, exp_month, exp_year = card_info[:3]
    cvc = card_info[3] if include_cvc and len(card_info) > 3 else None

    url = f"{PAYMENT_INTENT_URL}/{client_secret.split('_secret_')[0]}/confirm"

    payload = {
        'payment_method_data[type]': 'card',
        'payment_method_data[card][number]': card_number,
        'payment_method_data[card][exp_year]': exp_year,
        'payment_method_data[card][exp_month]': exp_month,
        'payment_method_data[billing_details][address][country]': 'IN',
        'key': public_key,
        'client_secret': client_secret
    }

    if cvc:
        payload['payment_method_data[card][cvc]'] = cvc
    if stripe_account:
        payload['_stripe_account'] = stripe_account

    response = requests.post(url, data=payload, headers=COMMON_HEADERS)
    return response.json()

def authenticate_3ds(source, public_key):
    """
    Handle the 3DS authentication step.
    """
    payload = {
        'source': source,
        'browser': '{"fingerprintAttempted":true,"fingerprintData":null,"challengeWindowSize":null,'
                   '"threeDSCompInd":"Y","browserJavaEnabled":true,"browserJavascriptEnabled":true,'
                   '"browserLanguage":"en-US","browserColorDepth":"24","browserScreenHeight":"800",'
                   '"browserScreenWidth":"360","browserTZ":"-330","browserUserAgent":'
                   '"Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) '
                   'Chrome/124.0.0.0 Mobile Safari/537.36"}',
        'key': public_key
    }

    requests.post(THREEDS_AUTHENTICATE_URL, data=payload, headers=COMMON_HEADERS)  # Ignore the response

def retrieve_payment_intent(payment_intent_id, public_key, stripe_account=None):
    """
    Retrieve the payment intent status after 3DS.
    """
    url = f"{PAYMENT_INTENT_URL}/{payment_intent_id}"

    params = {
        'key': public_key
    }

    if stripe_account:
        params['_stripe_account'] = stripe_account

    response = requests.get(url, params=params, headers=COMMON_HEADERS)
    return response.json()

def format_response(response):
    """
    Format the response to include the custom API owner tag.
    """
    return {
        "api owned by": "@HRK_07",
        "response": response
    }

@app.route('/inbuilt/ccn', methods=['GET'])
def inbuilt_ccn():
    """
    Endpoint to handle payment confirmation and 3DS flow.
    """
    try:
        public_key = request.args.get('pk')
        client_secret = request.args.get('cs')
        card_details = request.args.get('cc')
        stripe_account = request.args.get('act')

        # Step 1: Confirm Payment Intent
        confirm_response = confirm_payment_intent(client_secret, card_details, public_key, stripe_account, include_cvc=False)
        if 'error' in confirm_response:
            return jsonify(format_response(confirm_response)), 400

        # Step 2: Check if 3DS Authentication is Required
        if confirm_response.get('status') == 'requires_action':
            three_ds_source = confirm_response['next_action']['use_stripe_sdk']['three_d_secure_2_source']

            # Step 3: Authenticate 3DS
            authenticate_3ds(three_ds_source, public_key)  # No need to store or return the response

            # Step 4: Reconfirm Payment Intent after 3DS Authentication
            reconfirm_response = retrieve_payment_intent(client_secret, public_key, stripe_account)
            return jsonify(format_response(reconfirm_response))
        else:
            # No 3DS required, return the first confirmation response
            return jsonify(format_response(confirm_response))
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/inbuilt/cvv', methods=['GET'])
def inbuilt_cvv():
    """
    Endpoint to handle payment confirmation with CVC and 3DS flow.
    """
    try:
        public_key = request.args.get('pk')
        client_secret = request.args.get('cs')
        card_details = request.args.get('cc')
        stripe_account = request.args.get('act')

        # Step 1: Confirm Payment Intent with CVC
        confirm_response = confirm_payment_intent(client_secret, card_details, public_key, stripe_account, include_cvc=True)
        if 'error' in confirm_response:
            return jsonify(format_response(confirm_response)), 400

        # Step 2: Check if 3DS Authentication is Required
        if confirm_response.get('status') == 'requires_action':
            three_ds_source = confirm_response['next_action']['use_stripe_sdk']['three_d_secure_2_source']

            # Step 3: Authenticate 3DS
            authenticate_3ds(three_ds_source, public_key)  # No need to store or return the response

            # Step 4: Reconfirm Payment Intent after 3DS Authentication
            reconfirm_response = retrieve_payment_intent(client_secret, public_key, stripe_account)
            return jsonify(format_response(reconfirm_response))
        else:
            # No 3DS required, return the first confirmation response
            return jsonify(format_response(confirm_response))
    except Exception as e:
        return jsonify({'error': str(e)}), 400

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)
