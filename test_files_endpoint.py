#!/usr/bin/env python3
"""
Script para testar o endpoint /files da API John Deere
Endpoint: /files
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
SCOPES = "ag1 ag2 ag3 org1 eq1 files offline_access"  # Adicionando ag3 e files

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

def test_files_endpoint(filter_type="ALL", file_type=None, transferable=None, x_deere_signature=None):
    """
    Testa o endpoint /files com diferentes parâmetros
    """
    tokens = get_valid_tokens()
    if not tokens:
        return None
    
    access_token = tokens.get('access_token')
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Accept': 'application/vnd.deere.axiom.v3+json'
    }
    
    # Adicionar x-deere-signature se fornecido
    if x_deere_signature:
        headers['x-deere-signature'] = x_deere_signature
    
    # Construir URL com parâmetros
    url = f"{API_BASE_URL}/files"
    params = {}
    
    if filter_type:
        params['filter'] = filter_type
    
    if file_type is not None:
        params['fileType'] = file_type
    
    if transferable is not None:
        params['transferable'] = str(transferable).lower()
    
    print(f"📡 Testando endpoint: {url}")
    print(f"🔧 Parâmetros: {params}")
    print(f"📋 Headers: {headers}")
    
    try:
        response = requests.get(url, headers=headers, params=params)
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

def analyze_files_data(files_data):
    """
    Analisa os dados de arquivos recebidos
    """
    if not files_data:
        print("❌ Nenhum dado para analisar")
        return
    
    print("\n" + "="*80)
    print("📊 ANÁLISE DOS ARQUIVOS")
    print("="*80)
    
    # Verificar estrutura dos dados
    print(f"📋 Tipo de resposta: {type(files_data)}")
    print(f"📋 Chaves disponíveis: {list(files_data.keys()) if isinstance(files_data, dict) else 'N/A'}")
    
    if isinstance(files_data, dict):
        # Se é um dicionário, pode ter 'values' com a lista de arquivos
        files_list = files_data.get('values', [])
        total = files_data.get('total', len(files_list))
        print(f"📈 Total de arquivos: {total}")
        
        if files_list:
            print(f"\n📋 Primeiros 5 arquivos:")
            for i, file_info in enumerate(files_list[:5], 1):
                print(f"   {i}. {file_info}")
        
        # Salvar dados em arquivo
        output_file = "files_data.json"
        print(f"\n💾 Salvando dados em {output_file}...")
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(files_data, f, ensure_ascii=False, indent=2)
        
    elif isinstance(files_data, list):
        print(f"📈 Total de arquivos: {len(files_data)}")
        
        if files_data:
            print(f"\n📋 Primeiros 5 arquivos:")
            for i, file_info in enumerate(files_data[:5], 1):
                print(f"   {i}. {file_info}")
        
        # Salvar dados em arquivo
        output_file = "files_data.json"
        print(f"\n💾 Salvando dados em {output_file}...")
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(files_data, f, ensure_ascii=False, indent=2)
    
    else:
        print(f"📋 Conteúdo: {files_data}")

def test_different_filters():
    """
    Testa diferentes filtros do endpoint /files
    """
    print("🚀 Testando diferentes filtros do endpoint /files...")
    
    # Teste 1: Todos os arquivos (padrão)
    print("\n" + "="*60)
    print("🧪 TESTE 1: Todos os arquivos (filter=ALL)")
    print("="*60)
    result1 = test_files_endpoint(filter_type="ALL")
    analyze_files_data(result1)
    
    # Teste 2: Apenas arquivos de máquina
    print("\n" + "="*60)
    print("🧪 TESTE 2: Apenas arquivos de máquina (filter=MACHINE)")
    print("="*60)
    result2 = test_files_endpoint(filter_type="MACHINE")
    analyze_files_data(result2)
    
    # Teste 3: Arquivos transferíveis
    print("\n" + "="*60)
    print("🧪 TESTE 3: Arquivos transferíveis (transferable=true)")
    print("="*60)
    result3 = test_files_endpoint(transferable=True)
    analyze_files_data(result3)
    
    # Teste 4: Arquivos não transferíveis
    print("\n" + "="*60)
    print("🧪 TESTE 4: Arquivos não transferíveis (transferable=false)")
    print("="*60)
    result4 = test_files_endpoint(transferable=False)
    analyze_files_data(result4)
    
    # Teste 5: Sem filtros (padrão)
    print("\n" + "="*60)
    print("🧪 TESTE 5: Sem filtros (padrão)")
    print("="*60)
    result5 = test_files_endpoint()
    analyze_files_data(result5)

def main():
    """
    Função principal
    """
    print("🚀 Iniciando testes do endpoint /files...")
    
    # Verificar se temos os escopos necessários
    print(f"🔑 Escopos configurados: {SCOPES}")
    print("⚠️  Nota: Este endpoint requer os escopos 'files' e 'ag3'")
    
    # Testar diferentes filtros
    test_different_filters()
    
    print("\n✅ Testes concluídos!")

if __name__ == "__main__":
    main() 