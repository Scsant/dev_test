#!/usr/bin/env python3
"""
Script para testar o download correto de arquivos da API John Deere
Usando os headers Accept corretos para download do arquivo real
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

def test_file_download_with_headers(file_id: str, file_name: str, accept_header: str, test_name: str):
    """
    Testa o download do arquivo com diferentes headers Accept
    """
    tokens = get_valid_tokens()
    if not tokens:
        return None
    
    access_token = tokens.get('access_token')
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Accept': accept_header
    }
    
    url = f"{API_BASE_URL}/files/{file_id}"
    
    print(f"📡 Testando {test_name}: {url}")
    print(f"📋 Accept Header: {accept_header}")
    
    try:
        response = requests.get(url, headers=headers, stream=True)
        print(f"📊 Status: {response.status_code}")
        print(f"📋 Content-Type: {response.headers.get('Content-Type', 'N/A')}")
        print(f"📋 Content-Length: {response.headers.get('Content-Length', 'N/A')}")
        print(f"📋 Content-Disposition: {response.headers.get('Content-Disposition', 'N/A')}")
        
        if response.status_code == 200:
            # Criar diretório para downloads se não existir
            download_dir = "downloads"
            if not os.path.exists(download_dir):
                os.makedirs(download_dir)
            
            # Salvar arquivo
            safe_filename = "".join(c for c in file_name if c.isalnum() or c in (' ', '-', '_', '.')).rstrip()
            file_path = os.path.join(download_dir, f"{file_id}_{test_name}_{safe_filename}")
            
            with open(file_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            
            file_size = os.path.getsize(file_path)
            print(f"✅ Arquivo baixado: {file_path} ({file_size} bytes)")
            
            # Verificar se é um arquivo ZIP válido
            if file_path.endswith('.zip') or 'zip' in accept_header.lower():
                try:
                    import zipfile
                    with zipfile.ZipFile(file_path, 'r') as zip_ref:
                        file_list = zip_ref.namelist()
                        print(f"📦 Arquivo ZIP válido! Conteúdo: {file_list[:5]}...")
                except zipfile.BadZipFile:
                    print("⚠️ Arquivo não é um ZIP válido")
            
            # Tentar ler como texto se for pequeno e não for ZIP
            if file_size < 10000 and 'json' in accept_header.lower():
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    print(f"📄 Conteúdo JSON (primeiros 500 chars): {content[:500]}")
                except:
                    print("📄 Arquivo não é texto legível")
            
            return {
                'success': True,
                'file_path': file_path,
                'file_size': file_size,
                'content_type': response.headers.get('Content-Type'),
                'content_disposition': response.headers.get('Content-Disposition')
            }
        else:
            print(f"❌ Erro: {response.status_code}")
            print(f"📄 Resposta: {response.text}")
            return {'success': False, 'error': response.status_code}
            
    except Exception as e:
        print(f"❌ Erro na requisição: {e}")
        return {'success': False, 'error': str(e)}

def test_file_download_with_parameters(file_id: str, file_name: str, offset: int = -1, size: int = -1):
    """
    Testa o download do arquivo com parâmetros offset e size
    """
    tokens = get_valid_tokens()
    if not tokens:
        return None
    
    access_token = tokens.get('access_token')
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Accept': 'application/octet-stream'
    }
    
    params = {
        'offset': offset,
        'size': size
    }
    
    url = f"{API_BASE_URL}/files/{file_id}"
    
    print(f"📡 Testando download com parâmetros: {url}")
    print(f"📋 Parâmetros: offset={offset}, size={size}")
    
    try:
        response = requests.get(url, headers=headers, params=params, stream=True)
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
            file_path = os.path.join(download_dir, f"{file_id}_params_offset{offset}_size{size}_{safe_filename}")
            
            with open(file_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            
            file_size = os.path.getsize(file_path)
            print(f"✅ Arquivo baixado: {file_path} ({file_size} bytes)")
            
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

def load_files_data():
    """
    Carrega os dados dos arquivos para pegar alguns IDs de exemplo
    """
    if not os.path.exists('files_data.json'):
        print("❌ Arquivo files_data.json não encontrado. Execute test_files_endpoint.py primeiro.")
        return None
    
    with open('files_data.json', 'r', encoding='utf-8') as f:
        return json.load(f)

def get_sample_file_ids(files_data, count=2):
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
    print("🚀 Iniciando testes de download correto de arquivos...")
    
    # Carregar dados dos arquivos
    files_data = load_files_data()
    if not files_data:
        return
    
    # Pegar alguns IDs de arquivos para testar
    sample_files = get_sample_file_ids(files_data, 2)
    
    if not sample_files:
        print("❌ Nenhum arquivo encontrado para testar.")
        return
    
    print(f"📋 Testando download de {len(sample_files)} arquivos...")
    
    # Headers Accept para testar
    accept_headers = [
        ("application/zip", "ZIP"),
        ("application/octet-stream", "OCTET_STREAM"),
        ("application/x-zip", "X_ZIP"),
        ("application/x-zip-compressed", "X_ZIP_COMPRESSED"),
        ("multipart/mixed", "MULTIPART"),
        ("application/vnd.deere.axiom.v3+json", "JSON_METADATA")
    ]
    
    results = []
    
    for i, (file_id, file_name, file_size) in enumerate(sample_files, 1):
        print(f"\n" + "="*80)
        print(f"🧪 TESTE {i}: Arquivo {file_name} (ID: {file_id}, Tamanho: {file_size} bytes)")
        print(f"{'='*80}")
        
        file_results = {
            'file_id': file_id,
            'file_name': file_name,
            'file_size': file_size,
            'download_tests': {}
        }
        
        # Teste 1: Diferentes headers Accept
        print(f"\n📋 1. Testando diferentes headers Accept:")
        for accept_header, test_name in accept_headers:
            print(f"\n--- Teste {test_name} ---")
            result = test_file_download_with_headers(file_id, file_name, accept_header, test_name)
            file_results['download_tests'][test_name] = result
            time.sleep(1)  # Pausa entre requisições
        
        # Teste 2: Download com parâmetros
        print(f"\n📋 2. Testando download com parâmetros:")
        print(f"\n--- Download completo ---")
        result_params = test_file_download_with_parameters(file_id, file_name, -1, -1)
        file_results['download_tests']['PARAMS_COMPLETE'] = result_params
        
        results.append(file_results)
        
        # Pausa entre arquivos
        time.sleep(2)
    
    # Salvar resumo dos resultados
    summary_file = "download_correct_results.json"
    print(f"\n💾 Salvando resumo em {summary_file}...")
    with open(summary_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    # Estatísticas
    print(f"\n📊 RESUMO DOS TESTES:")
    for file_result in results:
        file_name = file_result['file_name']
        successful_tests = sum(1 for test_result in file_result['download_tests'].values() 
                             if test_result and test_result.get('success', False))
        total_tests = len(file_result['download_tests'])
        print(f"✅ {file_name}: {successful_tests}/{total_tests} testes bem-sucedidos")
    
    print(f"📁 Arquivos salvos em: ./downloads/")
    print(f"📋 Resumo salvo em: {summary_file}")
    
    print(f"\n✅ Testes de download correto concluídos!")

if __name__ == "__main__":
    main() 