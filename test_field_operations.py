#!/usr/bin/env python3
"""
Script para testar especificamente o endpoint de operações de campo
"""

import os
import json
import requests
import time
from typing import Optional, Dict, Any

API_BASE_URL = "https://sandboxapi.deere.com/platform"
TOKEN_URL = "https://signin.johndeere.com/oauth2/aus78tnlaysMraFhC1t7/v1/token"
CLIENT_ID = "0oap8bfnk7ViKFk7M5d7"
CLIENT_SECRET = "usklX-2OR8SHRY9pziQ-uMS3qzxkwYR_ZpFatiuQtFPaWVi6NrmhZW9RQvFjVYlL"
REDIRECT_URI = "http://localhost:9090/callback"
SCOPES = "ag1 ag2 org1 eq1 offline_access"

def load_tokens():
    if os.path.exists('tokens.json'):
        with open('tokens.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    return None

def save_tokens(tokens):
    with open('tokens.json', 'w', encoding='utf-8') as f:
        json.dump(tokens, f)

def is_token_expired_or_expiring(tokens, grace_period=60):
    access_token = tokens.get('access_token')
    expires_in = tokens.get('expires_in')
    token_acquired_time = tokens.get('token_acquired_time')
    if not access_token or not expires_in or not token_acquired_time:
        return True
    time_elapsed = time.time() - float(token_acquired_time)
    time_remaining = float(expires_in) - time_elapsed
    return time_remaining <= grace_period

def refresh_access_token(tokens):
    refresh_token = tokens.get('refresh_token')
    if not refresh_token:
        print("❌ Refresh Token não disponível.")
        return None
    
    print("🔄 Renovando access token...")
    headers = {
        'Accept': 'application/json',
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    data = {
        'grant_type': 'refresh_token',
        'refresh_token': refresh_token,
        'redirect_uri': REDIRECT_URI,
        'scope': SCOPES,
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET
    }
    
    try:
        response = requests.post(TOKEN_URL, headers=headers, data=data, verify=False)  # 'verify=True' para garantir que a conexão é segura
        response.raise_for_status()
        token_data = response.json()
        tokens['access_token'] = token_data.get('access_token')
        tokens['refresh_token'] = token_data.get('refresh_token', refresh_token)
        tokens['expires_in'] = token_data.get('expires_in')
        tokens['token_acquired_time'] = time.time()
        save_tokens(tokens)
        print("✅ Access token renovado!")
        return tokens
    except requests.exceptions.RequestException as e:
        print(f"❌ Erro ao renovar token: {e}")
        return None

def get_valid_tokens():
    tokens = load_tokens()
    if not tokens:
        print("❌ Tokens não encontrados. Execute jd.py primeiro.")
        return None
    
    if is_token_expired_or_expiring(tokens):
        tokens = refresh_access_token(tokens)
        if not tokens:
            print("❌ Falha ao renovar token.")
            return None
    
    return tokens


def test_field_operations_all_fields():
    """
    Itera sobre todos os campos do arquivo fields_organization_5881930.json e executa o TESTE 3 (cropSeason=2025) para cada campo.
    """
    tokens = get_valid_tokens()
    if not tokens:
        return

    access_token = tokens.get('access_token')
    organization_id = "5881930"

    # Carrega todos os campos do JSON
    with open('fields_organization_5881930.json', 'r', encoding='utf-8') as f:
        fields = json.load(f)

    headers = {
        'Authorization': f'Bearer {access_token}',
        'Accept': 'application/vnd.deere.axiom.v3+json'
    }

    results = []
    for field in fields:
        field_id = field['id']
        field_name = field.get('name', 'Sem nome')
        filtered_url = f"{API_BASE_URL}/organizations/{organization_id}/fields/{field_id}/fieldOperations?cropSeason=2025"
        print(f"\n{'='*60}")
        print(f"📋 TESTE 3: Campo {field_name} (ID: {field_id}) - Filtro cropSeason=2025")
        print(f"{'='*60}")
        print(f"📡 URL: {filtered_url}")

        field_result = {
            'id': field_id,
            'name': field_name,
            'url': filtered_url,
            'status_code': None,
            'data': None,
            'error': None
        }

        try:
            response = requests.get(filtered_url, headers=headers, verify=False)
            print(f"📊 Status: {response.status_code}")
            field_result['status_code'] = response.status_code

            if response.status_code == 200:
                data = response.json()
                print("✅ Sucesso! Operações filtradas:")
                print(json.dumps(data, indent=2))
                field_result['data'] = data
            else:
                print(f"❌ Erro {response.status_code}: {response.text}")
                field_result['error'] = response.text

        except Exception as e:
            print(f"❌ Exceção: {e}")
            field_result['error'] = str(e)

        results.append(field_result)

    # Salva todos os resultados em um arquivo JSON
    with open('field_operations_results_2025.json', 'w', encoding='utf-8') as fout:
        json.dump(results, fout, ensure_ascii=False, indent=2)
    print("\n📝 Resultados salvos em 'field_operations_results_2025.json'.")

if __name__ == "__main__":
    test_field_operations_all_fields()