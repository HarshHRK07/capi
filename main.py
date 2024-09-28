from flask import Flask, jsonify
import requests
import json
import random
import string

app = Flask(__name__)

def generate_random_username(length=8):
    letters = string.ascii_lowercase
    return ''.join(random.choice(letters) for i in range(length))

def get_random_email():
    domains = ["gmail.com", "yahoo.com", "outlook.com"]
    username = generate_random_username()
    domain = random.choice(domains)
    return f"{username}@{domain}"

# Proxy settings
proxies = {
    "http": "http://purevpn0s13830845:6phsLWXBQEq4MR@prox-hk.pointtoserver.com:10799"
}

@app.route('/', methods=['GET'])
def generate_client_secret():
    url1 = "https://ko-fi.com/Checkout/SetupDonation"

    payload1 = {
        "ReceiverPageId": "C1C3EPXR8",
        "Quantity": 1,
        "Amount": 1,
        "PrivateMessage": "false",
        "Message": "",
        "IsMembership": "false",
        "GuestName": "",
        "FlowStartedFrom": "ProfileDonationPanelPopup"
    }

    headers1 = {
        'User-Agent': "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Mobile Safari/537.36",
        'Accept': "application/json, text/javascript, */*; q=0.01",
        'Content-Type': "application/x-www-form-urlencoded; charset=UTF-8",
        'Origin': "https://ko-fi.com",
        'Referer': "https://ko-fi.com/wooqiart"
    }

    # Adding the proxy to the request
    response1 = requests.post(url1, data=payload1, headers=headers1, proxies=proxies)
    if response1.status_code != 200:
        return jsonify({
            "error": "Failed to setup donation",
            "status_code": response1.status_code,
            "response_text": response1.text
        }), 500

    try:
        response_data1 = response1.json()
    except json.JSONDecodeError:
        return jsonify({"error": "Invalid response from server", "response_text": response1.text}), 500

    transaction_id = response_data1.get("TransactionId")
    if not transaction_id:
        return jsonify({"error": "Failed to get transaction ID", "response_data": response_data1}), 500

    random_email = get_random_email()

    url2 = "https://ko-fi.com/api/checkout/start"

    payload2 = json.dumps({
        "transactionId": transaction_id,
        "buyerInformation": {
            "guestEmail": random_email,
            "guestName": None
        },
        "messageOfSupport": None,
        "isPrivateMessage": False,
        "paymentFlow": "STRIPE_PAYMENT_ELEMENT",
        "payWhatYouWantPrice": 1
    })

    headers2 = {
        'User-Agent': "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Mobile Safari/537.36",
        'Accept': "application/json",
        'Content-Type': "application/json",
        'Origin': "https://ko-fi.com",
        'Referer': "https://ko-fi.com/wooqiart"
    }

    # Adding the proxy to the request
    response2 = requests.post(url2, data=payload2, headers=headers2, proxies=proxies)
    if response2.status_code != 200:
        return jsonify({
            "error": "Failed to start checkout",
            "status_code": response2.status_code,
            "response_text": response2.text
        }), 500

    try:
        response_data2 = response2.json()
    except json.JSONDecodeError:
        return jsonify({"error": "Invalid response from server", "response_text": response2.text}), 500

    client_secret = response_data2.get("clientSecret")
    if not client_secret:
        return jsonify({"error": "Failed to get client secret", "response_data": response_data2}), 500

    pk = "pk_live_51B0RtLExmLtWgK8g8iuIDf43DrJw5rBS9yTLOxSiAeDiLnrSeM5NoEi8g6GBiVOGUkdovXFynKrJr8AltEpwqeX000myZ0W37g"

    output = {
        "client_secret": client_secret,
        "pk": pk
    }

    return jsonify(output)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
