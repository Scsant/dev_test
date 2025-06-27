import requests
import json

API_BASE_URL = "https://sandboxapi.deere.com/platform"

def load_tokens():
    with open('tokens.json', 'r', encoding='utf-8') as f:
        return json.load(f)

def get_clients(org_id, record_filter="ACTIVE"):
    tokens = load_tokens()
    access_token = tokens.get('access_token')
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Accept': 'application/vnd.deere.axiom.v3+json'
    }
    params = {'recordFilter': record_filter}
    url = f"{API_BASE_URL}/organizations/{org_id}/clients"
    response = requests.get(url, headers=headers, params=params, verify=False)
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(json.dumps(data, indent=2))
        return data
    else:
        print(f"Erro: {response.text}")
        return None

def get_client_fields(org_id, client_id, x_deere_signature=""):
    tokens = load_tokens()
    access_token = tokens.get('access_token')
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Accept': 'application/vnd.deere.axiom.v3+json',
        'x-deere-signature': x_deere_signature
    }
    url = f"{API_BASE_URL}/organizations/{org_id}/clients/{client_id}/fields"
    response = requests.get(url, headers=headers, verify=False)
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(json.dumps(data, indent=2))
        # Se precisar do novo x-deere-signature:
        signature = response.headers.get('x-deere-signature')
        print(f"x-deere-signature: {signature}")
        return data, signature
    else:
        print(f"Erro: {response.text}")
        return None, None

# Exemplo de uso:
if __name__ == "__main__":
    org_id = 5881930  # Substitua pelo seu orgId
    clients_data = get_clients(org_id)
    all_client_fields = []
    if clients_data and 'values' in clients_data:
        for client in clients_data['values']:
            client_id = client['id']
            print(f"\nBuscando campos do cliente {client_id}...")
            fields_data, signature = get_client_fields(org_id, client_id)
            all_client_fields.append({
                'client_id': client_id,
                'client_name': client.get('name'),
                'fields': fields_data,
                'x_deere_signature': signature
            })

    # Salva todos os resultados em um arquivo JSON
    with open('all_client_fields.json', 'w', encoding='utf-8') as f:
        json.dump(all_client_fields, f, ensure_ascii=False, indent=2)
    print("\n📝 Resultado salvo em 'all_client_fields.json'.")