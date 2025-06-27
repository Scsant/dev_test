#!/usr/bin/env python3
"""
Script para testar o endpoint fileActivities de um arquivo específico
Endpoint: /files/{fileId}/fileActivities
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

def test_file_activities(file_id: str):
    """
    Testa o endpoint fileActivities para um arquivo específico
    """
    tokens = get_valid_tokens()
    if not tokens:
        return None
    
    access_token = tokens.get('access_token')
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Accept': 'application/vnd.deere.axiom.v3+json'
    }
    
    url = f"{API_BASE_URL}/files/{file_id}/fileActivities"
    
    print(f"📡 Testando endpoint: {url}")
    print(f"📋 Headers: {headers}")
    
    try:
        response = requests.get(url, headers=headers, verify=False)  # 'verify=True' para garantir que a conexão é segura
        print(f"📊 Status: {response.status_code}")
        print(f"📋 Response Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Sucesso! Dados recebidos:")
            print(json.dumps(data, indent=2, ensure_ascii=False))
            return data
        else:
            print(f"❌ Erro: {response.status_code}")
            print(f"📄 Resposta: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Erro na requisição: {e}")
        return None

def test_file_details(file_id: str):
    """
    Testa o endpoint de detalhes do arquivo
    """
    tokens = get_valid_tokens()
    if not tokens:
        return None
    
    access_token = tokens.get('access_token')
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Accept': 'application/vnd.deere.axiom.v3+json'
    }
    
    url = f"{API_BASE_URL}/files/{file_id}"
    
    print(f"📡 Testando detalhes do arquivo: {url}")
    
    try:
        response = requests.get(url, headers=headers, verify=False)  # 'verify=True' para garantir que a conexão é segura
        print(f"📊 Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Sucesso! Detalhes do arquivo:")
            print(json.dumps(data, indent=2, ensure_ascii=False))
            return data
        else:
            print(f"❌ Erro: {response.status_code}")
            print(f"📄 Resposta: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Erro na requisição: {e}")
        return None

def test_file_partnerships(file_id: str):
    """
    Testa o endpoint de parcerias do arquivo
    """
    tokens = get_valid_tokens()
    if not tokens:
        return None
    
    access_token = tokens.get('access_token')
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Accept': 'application/vnd.deere.axiom.v3+json'
    }
    
    url = f"{API_BASE_URL}/files/{file_id}/partnerships"
    
    print(f"📡 Testando parcerias do arquivo: {url}")
    
    try:
        response = requests.get(url, headers=headers, verify=False)  # 'verify=True' para garantir que a conexão é segura   
        print(f"📊 Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Sucesso! Parcerias do arquivo:")
            print(json.dumps(data, indent=2, ensure_ascii=False))
            return data
        else:
            print(f"❌ Erro: {response.status_code}")
            print(f"📄 Resposta: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Erro na requisição: {e}")
        return None

def load_files_data():
    """
    Carrega os dados dos arquivos para pegar alguns IDs de exemplo
    """
    if not os.path.exists('files_data.json'):
        print("❌ Arquivo files_data.json não encontrado. Execute test_files_endpoint.py primeiro.")
        return None
    
    with open('files_data.json', 'r', encoding='utf-8') as f:
        return json.load(f)

def get_sample_file_ids(files_data, count=3):
    """
    Pega alguns IDs de arquivos para testar
    """
    if not files_data or 'values' not in files_data:
        return []
    
    files = files_data['values']
    sample_files = files[:count] if len(files) >= count else files
    
    file_ids = []
    for file_info in sample_files:
        file_id = file_info.get('id')
        file_name = file_info.get('name', 'N/A')
        if file_id:
            file_ids.append((file_id, file_name))
    
    return file_ids

def main():
    """
    Função principal
    """
    print("🚀 Iniciando testes do endpoint fileActivities...")
    
    # Carregar dados dos arquivos
    files_data = load_files_data()
    if not files_data:
        return
    
    # Pegar alguns IDs de arquivos para testar
    sample_files = get_sample_file_ids(files_data, 3)
    
    if not sample_files:
        print("❌ Nenhum arquivo encontrado para testar.")
        return
    
    print(f"📋 Testando {len(sample_files)} arquivos...")
    
    for i, (file_id, file_name) in enumerate(sample_files, 1):
        print(f"\n" + "="*80)
        print(f"🧪 TESTE {i}: Arquivo {file_name} (ID: {file_id})")
        print(f"{'='*80}")
        
        # Teste 1: Detalhes do arquivo
        print(f"\n📋 1. Detalhes do arquivo:")
        file_details = test_file_details(file_id)
        
        # Teste 2: Atividades do arquivo
        print(f"\n📋 2. Atividades do arquivo:")
        file_activities = test_file_activities(file_id)
        
        # Teste 3: Parcerias do arquivo
        print(f"\n📋 3. Parcerias do arquivo:")
        file_partnerships = test_file_partnerships(file_id)
        
        # Salvar resultados
        results = {
            'file_id': file_id,
            'file_name': file_name,
            'details': file_details,
            'activities': file_activities,
            'partnerships': file_partnerships
        }
        
        output_file = f"file_analysis_{file_id}.json"
        print(f"\n💾 Salvando análise em {output_file}...")
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        
        # Pequena pausa entre requisições
        time.sleep(1)
    
    print(f"\n✅ Testes concluídos!")

if __name__ == "__main__":
    main() 