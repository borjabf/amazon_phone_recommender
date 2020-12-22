import requests

url = "https://x8ss55myg0.execute-api.eu-west-2.amazonaws.com/development/telefonos"

payload="{\"limit\": 10, \"Precio\": 200}"
headers = {
  'x-api-key': [token],
  'Content-Type': 'application/json'
}

response = requests.request("GET", url, headers=headers, data=payload)

print(response.text)
