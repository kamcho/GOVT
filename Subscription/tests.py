import base64
import datetime
import json
from requests.auth import HTTPBasicAuth
from django.http import JsonResponse
import requests

# from Finance.models import StudentFeeMpesaTransaction

# from Support.views import access_token

def generate_access_token():
    access_token_url = 'https://api.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials'
    consumer_key = "aSG8gGG7GWSGapToKz8ySyALUx9zIdbBr1CHldVhyOLjJsCz"
    consumer_secret = "o8qwdbzapgcvOd1lsBOkKGCL4JwMQyG9ZmKlKC7uaLIc4FsRJFbzfV10EAoL0P6u"

    # make a get request using python requests liblary
    response = requests.get(access_token_url, auth=HTTPBasicAuth(consumer_key, consumer_secret))

    # return access_token from response
    if response.status_code == 200:
        access_token = response.json()['access_token']        
        return access_token
    else:
        return None


def initiate_payment(phone):
    # phone=process_number(phone)
    paybill = "4161900"
    timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    consumer_key = 'fa0e41448ce844d1a7a37553cee8bf22b61fec894e1ce3e9c0e32b1c6953b6d9'
    concatenated_string = f"{paybill}{consumer_key}{timestamp}"
    base64_encoded = base64.b64encode(concatenated_string.encode()).decode('utf-8')
    password = str(base64_encoded)
    access_token = generate_access_token()
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }

    payload = {
        "BusinessShortCode": 4161900,  # Use double quotes for all keys and values
        "Password": password,  # Use the generated password
        "Timestamp": timestamp,
        "TransactionType": "CustomerPayBillOnline",
        "Amount": 1,
        "PartyA": phone,
        "PartyB": 4161900,
        "PhoneNumber": phone,
        "CallBackURL": "https://knowedge.online/Subscription/callback/",
        "AccountReference": "CompanyXLTD",
        "TransactionDesc": "Subscription",

    }

    responses = requests.request("POST", 'https://api.safaricom.co.ke/mpesa/stkpush/v1/processrequest', headers = headers, json = payload)
    if responses.status_code == 200:
        data = responses.text
        data = json.loads(data)
        checkout_id = data["CheckoutRequestID"]
        print(data)
    
        # paymentMetadata(user=user, checkout_id=checkout_id, subscription=subscription, phone=phone, beneficiaries=beneficiaries)
    print(responses)
    return responses

initiate_payment('254742134431')