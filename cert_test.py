import os
import requests

# Пути к файлам сертификатов
client_cert_path = 'client_cert.crt'
client_key_path = 'private.key'
ca_cert_path = 'cert.pem'

# Проверка существования файлов сертификатов
for cert_file in [client_cert_path, client_key_path, ca_cert_path]:
    if not os.path.isfile(cert_file):
        raise FileNotFoundError(f"Certificate file not found: {cert_file}")

url = 'https://mc.api.sberbank.ru/prod/tokens/v3/oauth'
payload = 'grant_type=client_credentials&scope=https://api.sberbank.ru/escrow'
headers = {
    'Authorization': 'Basic ',
    'RqUID': '25Ec70328e4CE4DF39e828E1dF75EFa0',
    'Content-Type': 'application/x-www-form-urlencoded'
}

client_cert = (client_cert_path, client_key_path)

try:
    response = requests.post(url, headers=headers, data=payload, verify="cacerts.cer")
    print(response.json())
except requests.exceptions.RequestException as e:
    print(f"Error: {e}")