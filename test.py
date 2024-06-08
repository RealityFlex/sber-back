import requests
import ssl
import http.client

url = 'https://mc.api.sberbank.ru/prod/tokens/v3/oauth'
payload = 'grant_type=client_credentials&scope=https://api.sberbank.ru/escrow'
headers = {
    'Authorization': 'Basic ',
    'RqUID': '25Ec70328e4CE4DF39e828E1dF75EFa0',
    'Content-Type': 'application/x-www-form-urlencoded'
}

certificate_password = "78RUIUne"

# Пути к файлам сертификатов
cert = 'client_cert.crt'
key = 'private.key'

context = ssl.SSLContext(ssl.PROTOCOL_SSLv23)
context.load_cert_chain(cert, key, password=certificate_password)
context.verify_mode = ssl.CERT_REQUIRED
context.check_hostname = True

conn = http.client.HTTPSConnection("mc.api.sberbank.ru", 443, context=context)

conn.request("POST", "/prod/tokens/v3/oauth", payload, headers)
print(conn.getresponse())
# try:
#     response = requests.post(url, headers=headers, data=payload, verify=ca_cert)
#     print(response.json())
# except requests.exceptions.RequestException as e:
#     print(f"Error: {e}")
