from flask import Flask, request, jsonify
import requests
from bs4 import BeautifulSoup

app = Flask(__name__)

@app.route('/lookup', methods=['GET'])
def lookup_routing_number():
    # Get the routing number from the query parameters
    routing_number = request.args.get('routing')
    
    if not routing_number:
        return jsonify({
            "error": "Please provide a routing number.",
            "message": "an api by Harsh"
        }), 400

    url = "https://www.theswiftcodes.com/routing-number-checker/"
    payload = {'routing': routing_number}

    headers = {
        'User-Agent': "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Mobile Safari/537.36",
        'Accept': "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        'Content-Type': "application/x-www-form-urlencoded",
        'origin': "https://www.theswiftcodes.com",
        'sec-fetch-site': "same-origin",
        'sec-fetch-dest': "document",
        'referer': "https://www.theswiftcodes.com/routing-number-checker/"
    }

    # Make a POST request to the external site with the routing number
    response = requests.post(url, data=payload, headers=headers)

    # Parse the response HTML using BeautifulSoup
    soup = BeautifulSoup(response.text, 'html.parser')

    # Extract the relevant part of the table
    table = soup.find('table', class_='swift-detail')

    # Check if the table exists
    if table:
        rows = table.find_all('tr')

        # Create a dictionary to store the result
        result = {}

        # Loop through the rows and extract the key-value pairs
        for row in rows:
            key = row.find('th').text.strip()  # Extract the table header text
            value = row.find('td').text.strip()  # Extract the table data text
            result[key] = value

        # Add the message to the response
        result["message"] = "an api by Harsh"
        # Return the result as JSON
        return jsonify(result), 200
    else:
        # If the table is not found, return an error message
        return jsonify({
            "error": "Please provide a valid routing number.",
            "message": "an api by Harsh"
        }), 400

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)
  
