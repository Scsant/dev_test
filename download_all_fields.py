#!/usr/bin/env python3
"""
Script para testar o download de arquivos da API John Deere
Endpoints: /files/{fileId} e /files/{fileId}/presignedDownload
"""

import os
import json
import requests
import time
from typing import Optional, Dict, Any, List
import urllib.parse

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

def test_direct_download(file_id: str, file_name: str):
    """
    Testa o download direto do arquivo usando o endpoint /files/{fileId}
    """
    tokens = get_valid_tokens()
    if not tokens:
        return None
    
    access_token = tokens.get('access_token')
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Accept': '*/*'  # Aceita qualquer tipo de conteúdo
    }
    
    url = f"{API_BASE_URL}/files/{file_id}"
    
    print(f"📡 Testando download direto: {url}")
    
    try:
        response = requests.get(url, headers=headers, stream=True)
        print(f"📊 Status: {response.status_code}")
        print(f"📋 Content-Type: {response.headers.get('Content-Type', 'N/A')}")
        print(f"📋 Content-Length: {response.headers.get('Content-Length', 'N/A')}")
        
        if response.status_code == 200:
            # Criar diretório para downloads se não existir
            download_dir = "downloads"
            if not os.path.exists(download_dir):
                os.makedirs(download_dir)
            
            # Salvar arquivo
            safe_filename = "".join(c for c in file_name if c.isalnum() or c in (' ', '-', '_', '.')).rstrip()
            file_path = os.path.join(download_dir, f"{file_id}_{safe_filename}")
            
            with open(file_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            
            file_size = os.path.getsize(file_path)
            print(f"✅ Arquivo baixado: {file_path} ({file_size} bytes)")
            
            # Tentar ler como texto se for pequeno
            if file_size < 10000:  # Menos de 10KB
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    print(f"📄 Conteúdo (primeiros 500 chars): {content[:500]}")
                except:
                    print("📄 Arquivo não é texto legível")
            
            return {
                'success': True,
                'file_path': file_path,
                'file_size': file_size,
                'content_type': response.headers.get('Content-Type')
            }
        else:
            print(f"❌ Erro: {response.status_code}")
            print(f"📄 Resposta: {response.text}")
            return {'success': False, 'error': response.status_code}
            
    except Exception as e:
        print(f"❌ Erro na requisição: {e}")
        return {'success': False, 'error': str(e)}

def test_presigned_download(file_id: str, file_name: str):
    """
    Testa o download usando URL pré-assinada
    """
    tokens = get_valid_tokens()
    if not tokens:
        return None
    
    access_token = tokens.get('access_token')
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Accept': 'application/vnd.deere.axiom.v3+json'
    }
    
    url = f"{API_BASE_URL}/files/{file_id}/presignedDownload"
    
    print(f"📡 Obtendo URL pré-assinada: {url}")
    
    try:
        response = requests.get(url, headers=headers)
        print(f"📊 Status: {response.status_code}")
        
        if response.status_code == 200:
            presigned_data = response.json()
            print(f"✅ URL pré-assinada obtida:")
            print(json.dumps(presigned_data, indent=2))
            
            # Extrair URL de download
            download_url = presigned_data.get('uri') or presigned_data.get('url')
            if not download_url:
                print("❌ URL de download não encontrada na resposta")
                return {'success': False, 'error': 'URL não encontrada'}
            
            print(f"📡 Fazendo download via URL pré-assinada: {download_url}")
            
            # Download usando a URL pré-assinada (sem autenticação adicional)
            download_response = requests.get(download_url, stream=True)
            print(f"📊 Status do download: {download_response.status_code}")
            
            if download_response.status_code == 200:
                # Criar diretório para downloads se não existir
                download_dir = "downloads"
                if not os.path.exists(download_dir):
                    os.makedirs(download_dir)
                
                # Salvar arquivo
                safe_filename = "".join(c for c in file_name if c.isalnum() or c in (' ', '-', '_', '.')).rstrip()
                file_path = os.path.join(download_dir, f"{file_id}_presigned_{safe_filename}")
                
                with open(file_path, 'wb') as f:
                    for chunk in download_response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                
                file_size = os.path.getsize(file_path)
                print(f"✅ Arquivo baixado via presigned: {file_path} ({file_size} bytes)")
                
                return {
                    'success': True,
                    'file_path': file_path,
                    'file_size': file_size,
                    'presigned_data': presigned_data
                }
            else:
                print(f"❌ Erro no download: {download_response.status_code}")
                return {'success': False, 'error': download_response.status_code}
        else:
            print(f"❌ Erro ao obter URL pré-assinada: {response.status_code}")
            print(f"📄 Resposta: {response.text}")
            return {'success': False, 'error': response.status_code}
            
    except Exception as e:
        print(f"❌ Erro na requisição: {e}")
        return {'success': False, 'error': str(e)}

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
    # Filtrar apenas arquivos pequenos para teste (menos de 1MB)
    small_files = [f for f in files if f.get('nativeSize', 0) < 1000000]
    sample_files = small_files[:count] if len(small_files) >= count else files[:count]
    
    file_ids = []
    for file_info in sample_files:
        file_id = file_info.get('id')
        file_name = file_info.get('name', 'N/A')
        file_size = file_info.get('nativeSize', 0)
        if file_id:
            file_ids.append((file_id, file_name, file_size))
    
    return file_ids

def main():
    """
    Função principal
    """
    print("🚀 Iniciando testes de download de arquivos...")
    
    # Carregar dados dos arquivos
    files_data = load_files_data()
    if not files_data:
        return
    
    # Pegar alguns IDs de arquivos para testar
    sample_files = get_sample_file_ids(files_data, 3)
    
    if not sample_files:
        print("❌ Nenhum arquivo encontrado para testar.")
        return
    
    print(f"📋 Testando download de {len(sample_files)} arquivos...")
    
    results = []
    
    for i, (file_id, file_name, file_size) in enumerate(sample_files, 1):
        print(f"\n" + "="*80)
        print(f"🧪 TESTE {i}: Arquivo {file_name} (ID: {file_id}, Tamanho: {file_size} bytes)")
        print(f"{'='*80}")
        
        # Teste 1: Download direto
        print(f"\n📋 1. Download direto:")
        direct_result = test_direct_download(file_id, file_name)
        
        # Teste 2: Download via presigned URL
        print(f"\n📋 2. Download via presigned URL:")
        presigned_result = test_presigned_download(file_id, file_name)
        
        # Salvar resultados
        file_result = {
            'file_id': file_id,
            'file_name': file_name,
            'file_size': file_size,
            'direct_download': direct_result,
            'presigned_download': presigned_result
        }
        
        results.append(file_result)
        
        # Pequena pausa entre requisições
        time.sleep(2)
    
    # Salvar resumo dos resultados
    summary_file = "download_results.json"
    print(f"\n💾 Salvando resumo em {summary_file}...")
    with open(summary_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    # Estatísticas
    successful_direct = sum(1 for r in results if r['direct_download'].get('success', False))
    successful_presigned = sum(1 for r in results if r['presigned_download'].get('success', False))
    
    print(f"\n📊 RESUMO DOS TESTES:")
    print(f"✅ Downloads diretos bem-sucedidos: {successful_direct}/{len(results)}")
    print(f"✅ Downloads presigned bem-sucedidos: {successful_presigned}/{len(results)}")
    print(f"📁 Arquivos salvos em: ./downloads/")
    print(f"📋 Resumo salvo em: {summary_file}")
    
    print(f"\n✅ Testes de download concluídos!")

if __name__ == "__main__":
    main() 