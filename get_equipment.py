import json
import requests

API_EQUIPMENT_URL = "https://equipmentapi.deere.com/isg/equipment"

def load_tokens():
    with open('tokens.json', 'r', encoding='utf-8') as f:
        return json.load(f)

def get_equipment(organization_ids=None, serial_numbers=None, categories=None, item_limit=100):
    tokens = load_tokens()
    access_token = tokens.get('access_token')
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Accept': 'application/json'
    }
    params = {}
    if organization_ids:
        params['organizationIds'] = ','.join(str(org) for org in organization_ids)
    if serial_numbers:
        params['serialNumbers'] = ','.join(serial_numbers)
    if categories:
        params['categories'] = ','.join(categories)
    if item_limit:
        params['itemLimit'] = item_limit

    response = requests.get(API_EQUIPMENT_URL, headers=headers, params=params, verify=False)
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(json.dumps(data, indent=2))
        # Salvar resultado em arquivo, se desejar:
        with open('equipment_results.json', 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print("📝 Resultado salvo em 'equipment_results.json'")
    else:
        print(f"Erro: {response.text}")

if __name__ == "__main__":
    # Exemplo: buscar equipamentos da organização 5881930
    get_equipment(organization_ids=[5881930])