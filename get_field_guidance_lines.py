#!/usr/bin/env python3
"""
Script para buscar guidance lines de um campo da organização John Deere
Endpoint: /organizations/{orgId}/fields/{fieldId}/guidanceLines
"""

import os
import json
import requests
import time
from typing import Optional, Dict, Any, List

API_BASE_URL = "https://sandboxapi.deere.com/platform"
TOKEN_URL = "https://signin.johndeere.com/oauth2/aus78tnlaysMraFhC1t7/v1/token"
CLIENT_ID = "0oap8bfnk7ViKFk7M5d7"
CLIENT_SECRET = "usklX-2OR8SHRY9pziQ-uMS3qzxkwYR_ZpFatiuQtFPaWVi6NrmhZW9RQvFjVYlL"
REDIRECT_URI = "http://localhost:9090/callback"
SCOPES = "ag1 ag2 ag3 org1 eq1 files offline_access"
ORG_ID = "5881930"


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

def get_first_field_id():
    if not os.path.exists('fields_organization_5881930.json'):
        print("❌ Arquivo fields_organization_5881930.json não encontrado.")
        return None
    with open('fields_organization_5881930.json', 'r', encoding='utf-8') as f:
        fields = json.load(f)
    if isinstance(fields, list) and fields:
        return fields[0].get('id')
    print("❌ Nenhum campo encontrado no arquivo.")
    return None

def get_guidance_lines(org_id: str, field_id: str, status: str = "available", embed: Optional[str] = None):
    tokens = get_valid_tokens()
    if not tokens:
        return None
    access_token = tokens.get('access_token')
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Accept': 'application/vnd.deere.axiom.v3+json'
    }
    params = {"status": status}
    if embed:
        params["embed"] = embed
    url = f"{API_BASE_URL}/organizations/{org_id}/fields/{field_id}/guidanceLines"
    print(f"📡 Buscando guidance lines: {url}")
    try:
        response = requests.get(url, headers=headers, params=params)
        print(f"📊 Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Sucesso! {len(data.get('values', []))} guidance lines encontradas.")
            with open(f"guidance_lines_{field_id}.json", 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            return data
        else:
            print(f"❌ Erro: {response.status_code}")
            print(f"📄 Resposta: {response.text}")
            return None
    except Exception as e:
        print(f"❌ Erro na requisição: {e}")
        return None

def main():
    print("🚀 Buscando guidance lines do primeiro campo...")
    field_id = get_first_field_id()
    if not field_id:
        print("❌ Não foi possível obter um fieldId.")
        return
    data = get_guidance_lines(ORG_ID, field_id)
    if data:
        print(f"🔗 Dados salvos em guidance_lines_{field_id}.json")
        values = data.get('values', [])
        print(f"\nResumo dos primeiros 3 guidance lines:")
        for g in values[:3]:
            print(f"ID: {g.get('id')}, Nome: {g.get('name')}, Tipo: {g.get('type')}, Status: {g.get('status')}")
    else:
        print("Nenhum dado retornado.")

if __name__ == "__main__":
    main() 