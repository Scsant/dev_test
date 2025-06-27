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
        response = requests.post(TOKEN_URL, headers=headers, data=data)
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

def test_field_operations_endpoint():
    """
    Testa o endpoint de operações de campo
    """
    tokens = get_valid_tokens()
    if not tokens:
        return
    
    access_token = tokens.get('access_token')
    organization_id = "5881930"
    field_id = "19f73266-741a-99e1-3c04-a513c7481e3f"  # Primeiro campo da lista
    
    print(f"🧪 Testando endpoint de operações de campo...")
    print(f"   • Organização: {organization_id}")
    print(f"   • Campo: {field_id}")
    
    # Teste 1: Endpoint básico de operações de campo
    print(f"\n{'='*60}")
    print("📋 TESTE 1: Endpoint básico de operações de campo")
    print(f"{'='*60}")
    
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Accept': 'application/vnd.deere.axiom.v3+json'
    }
    
    field_ops_url = f"{API_BASE_URL}/organizations/{organization_id}/fields/{field_id}/fieldOperations"
    
    try:
        print(f"📡 URL: {field_ops_url}")
        print(f"📋 Headers: {headers}")
        
        response = requests.get(field_ops_url, headers=headers)
        
        print(f"📊 Status: {response.status_code}")
        print(f"📋 Response Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Sucesso! Dados recebidos:")
            print(json.dumps(data, indent=2))
        else:
            print(f"❌ Erro {response.status_code}: {response.text}")
            
    except Exception as e:
        print(f"❌ Exceção: {e}")
    
    # Teste 2: Endpoint de última operação de campo
    print(f"\n{'='*60}")
    print("📋 TESTE 2: Última operação de campo")
    print(f"{'='*60}")
    
    last_op_url = f"{field_ops_url}?lastFieldOperation=true"
    
    try:
        print(f"📡 URL: {last_op_url}")
        
        response = requests.get(last_op_url, headers=headers)
        
        print(f"📊 Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Sucesso! Última operação:")
            print(json.dumps(data, indent=2))
        else:
            print(f"❌ Erro {response.status_code}: {response.text}")
            
    except Exception as e:
        print(f"❌ Exceção: {e}")
    
    # Teste 3: Com parâmetros de filtro
    print(f"\n{'='*60}")
    print("📋 TESTE 3: Com filtros (cropSeason=2025)")
    print(f"{'='*60}")
    
    filtered_url = f"{field_ops_url}?cropSeason=2025"
    
    try:
        print(f"📡 URL: {filtered_url}")
        
        response = requests.get(filtered_url, headers=headers)
        
        print(f"📊 Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Sucesso! Operações filtradas:")
            print(json.dumps(data, indent=2))
        else:
            print(f"❌ Erro {response.status_code}: {response.text}")
            
    except Exception as e:
        print(f"❌ Exceção: {e}")

if __name__ == "__main__":
    test_field_operations_endpoint() 