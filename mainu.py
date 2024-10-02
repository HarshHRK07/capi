from flask import Flask, request, jsonify
import requests
import logging

app = Flask(__name__)

# Configure logging
logging.basicConfig(level=logging.INFO)

# Define URLs
PAYMENT_INTENT_URL = "https://api.stripe.com/v1/payment_intents"
THREEDS_AUTHENTICATE_URL = "https://api.stripe.com/v1/3ds2/authenticate"

# Define common headers
COMMON_HEADERS = {
    'User-Agent': "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Mobile Safari/537.36",
    'Accept': "application/json",
    'Content-Type': "application/x-www-form-urlencoded",
    'origin': "https://js.stripe.com",
    'sec-fetch-site': "same-site",
    'sec-fetch-mode': "cors",
    'referer': "https://js.stripe.com/"
}

# Improved payment intent confirmation with payment method
def confirm_payment_intent_with_payment_method(client_secret, card_details, public_key, stripe_account=None, include_cvc=False):
    try:
        # Split and extract card details
        card_info = card_details.split('|')
        card_number = card_info[0]
        exp_month = card_info[1]
        exp_year = card_info[2]
        cvc = card_info[3] if include_cvc and len(card_info) > 3 else None

        # Construct payload as a dictionary
        payload = {
            "payment_method_data[type]": "card",
            "payment_method_data[card][number]": card_number,
            "payment_method_data[card][exp_month]": exp_month,
            "payment_method_data[card][exp_year]": exp_year,
            "payment_method_data[billing_details][address][country]": "IN",
            "key": public_key,
            "client_secret": client_secret
        }
        if cvc:
            payload["payment_method_data[card][cvc]"] = cvc
        if stripe_account:
            payload["_stripe_account"] = stripe_account

        url = f"{PAYMENT_INTENT_URL}/{client_secret.split('_secret_')[0]}/confirm"
        response = requests.post(url, data=payload, headers=COMMON_HEADERS, timeout=30)
        return response.json()
    except requests.exceptions.RequestException as e:
        app.logger.error(f"Request failed: {str(e)}")
        return {'error': f"Request error: {str(e)}"}
    except Exception as e:
        app.logger.error(f"Unhandled error: {str(e)}")
        return {'error': f"Unhandled error: {str(e)}"}

# Improved 3DS authentication
def authenticate_3ds(source, client_secret, public_key):
    try:
        payload = {
            "source": source,
            "browser": '{"fingerprintAttempted":true,"fingerprintData":null,"challengeWindowSize":null,"threeDSCompInd":"Y",'
                       '"browserJavaEnabled":true,"browserJavascriptEnabled":true,"browserLanguage":"en-US","browserColorDepth":"24",'
                       '"browserScreenHeight":"800","browserScreenWidth":"360","browserTZ":"-330","browserUserAgent":'
                       '"Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Mobile Safari/537.36"}',
            "one_click_authn_device_support[hosted]": False,
            "one_click_authn_device_support[same_origin_frame]": False,
            "one_click_authn_device_support[spc_eligible]": False,
            "one_click_authn_device_support[webauthn_eligible]": False,
            "one_click_authn_device_support[publickey_credentials_get_allowed]": True,
            "key": public_key
        }
        response = requests.post(THREEDS_AUTHENTICATE_URL, data=payload, headers=COMMON_HEADERS, timeout=30)
        return response.json()
    except requests.exceptions.RequestException as e:
        app.logger.error(f"3DS authentication failed: {str(e)}")
        return {'error': f"3DS authentication error: {str(e)}"}
    except Exception as e:
        app.logger.error(f"Unhandled error: {str(e)}")
        return {'error': f"Unhandled error: {str(e)}"}

# Confirm payment intent after 3DS authentication
def confirm_payment_intent_after_3ds(payment_intent_id, client_secret, public_key, stripe_account=None):
    try:
        url = f"{PAYMENT_INTENT_URL}/{payment_intent_id}"
        params = {
            'key': public_key,
            'client_secret': client_secret
        }
        if stripe_account:
            params['_stripe_account'] = stripe_account

        response = requests.get(url, params=params, headers=COMMON_HEADERS, timeout=30)
        return response.json()
    except requests.exceptions.RequestException as e:
        app.logger.error(f"Failed to confirm payment intent after 3DS: {str(e)}")
        return {'error': f"Request error: {str(e)}"}
    except Exception as e:
        app.logger.error(f"Unhandled error: {str(e)}")
        return {'error': f"Unhandled error: {str(e)}"}

# Format response with consistent structure
def format_response(response):
    try:
        return {
            "api owned by": "@HRK_07",
            "response": response
        }
    except Exception as e:
        app.logger.error(f"Error formatting response: {str(e)}")
        return {'error': f"Error formatting response: {str(e)}"}

# Route for card details without CVC
@app.route('/inbuilt/ccn', methods=['POST'])
def inbuilt_ccn():
    try:
        data = request.get_json()
        public_key = data.get('pk')
        client_secret = data.get('cs')
        card_details = data.get('cc')
        stripe_account = data.get('act')

        if not all([public_key, client_secret, card_details]):
            return jsonify({'error': 'Missing required parameters'}), 400

        first_confirm_response = confirm_payment_intent_with_payment_method(client_secret, card_details, public_key, stripe_account, include_cvc=False)
        if 'error' in first_confirm_response:
            return jsonify(format_response(first_confirm_response)), 400

        if first_confirm_response.get('status') == 'requires_action':
            three_ds_source = first_confirm_response['next_action']['use_stripe_sdk']['three_d_secure_2_source']
            auth_response = authenticate_3ds(three_ds_source, client_secret, public_key)
            if 'error' in auth_response:
                return jsonify(format_response(auth_response)), 400

            if auth_response.get('state') == 'succeeded':
                final_response = confirm_payment_intent_after_3ds(first_confirm_response['id'], client_secret, public_key, stripe_account)
                if 'error' in final_response:
                    return jsonify(format_response(final_response)), 400
            else:
                final_response = auth_response
        else:
            final_response = first_confirm_response

        return jsonify(format_response(final_response))
    except Exception as e:
        app.logger.error(f"Error processing /inbuilt/ccn: {str(e)}")
        return jsonify({'error': str(e)}), 400

# Route for card details with CVC
@app.route('/inbuilt/cvv', methods=['POST'])
def inbuilt_cvv():
    try:
        data = request.get_json()
        public_key = data.get('pk')
        client_secret = data.get('cs')
        card_details = data.get('cc')
        stripe_account = data.get('act')

        if not all([public_key, client_secret, card_details]):
            return jsonify({'error': 'Missing required parameters'}), 400

        first_confirm_response = confirm_payment_intent_with_payment_method(client_secret, card_details, public_key, stripe_account, include_cvc=True)
        if 'error' in first_confirm_response:
            return jsonify(format_response(first_confirm_response)), 400

        if first_confirm_response.get('status') == 'requires_action':
            three_ds_source = first_confirm_response['next_action']['use_stripe_sdk']['three_d_secure_2_source']
            auth_response = authenticate_3ds(three_ds_source, client_secret, public_key)
            if 'error' in auth_response:
                return jsonify(format_response(auth_response)), 400

            if auth_response.get('state') == 'succeeded':
                final_response = confirm_payment_intent_after_3ds(first_confirm_response['id'], client_secret, public_key, stripe_account)
                if 'error' in final_response:
                    return jsonify(format_response(final_response)), 400
            else:
                final_response = auth_response
        else:
            final_response = first_confirm_response

        return jsonify(format_response(final_response))
    except Exception as e:
        app.logger.error(f"Error processing /inbuilt/cvv: {str(e)}")
        return jsonify({'error': str(e)}), 400

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)
