import requests


def get_token():
    
# Replace 'your_api_key_here', 'your_merchant_code_here', and 'your_consumer_secret_here' with actual values
    api_key = '94g4l74GEt4qgDSWGdMw+jxGQnwO8v6gYyTNOslM7LQ0mGQUyRtlGE6O8O2AajeFrd6KSVR32fRRMFoYZYpkIQ=='
    merchant_code = '9401576880'
    consumer_secret = 'h907DIcM26cQUh3z2c7OxzgHKO98rT'

    # Define the endpoint URLs for test and live environments
    test_url = 'https://uat.finserve.africa/authentication/api/v3/authenticate/merchant'
    live_url = 'https://api.finserve.africa/authentication/api/v3/authenticate/merchant'

    # Define the headers required for the request
    headers = {
        'Content-Type': 'application/json',
        'Api-Key': api_key
    }

    # Define the request body containing merchantCode and consumerSecret
    data = {
        'merchantCode': merchant_code,
        'consumerSecret': consumer_secret
    }

    try:
        # Make the HTTP POST request to the authentication endpoint
        response = requests.post(test_url, headers=headers, json=data)

        # Check if the request was successful (status code 200)
        if response.status_code == 200:
            # Parse the JSON response to extract the access token
            token_data = response.json()
            access_token = token_data['accessToken']
            
            return access_token
        else:
            print(f"Error: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"An error occurred: {e}")
# get_token()
# Replace 'your_api_key_here' and 'your_transaction_reference_here' with actual values
def get_transaction():
    api_key = '94g4l74GEt4qgDSWGdMw+jxGQnwO8v6gYyTNOslM7LQ0mGQUyRtlGE6O8O2AajeFrd6KSVR32fRRMFoYZYpkIQ=='
    transaction_reference = '10120120098767'

    endpoint = f'https://uat.finserve.africa/v3-apis/transaction-api/v3.0/transactions/details/{transaction_reference}'
    token = get_token()
    # print(token)
    
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }

    try:
        response = requests.get(endpoint, headers=headers)
        if response.status_code == 200:
            transaction_details = response.json()
            print(transaction_details)
        else:
            print(f"Error: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"An error occurred: {e}")

get_transaction()