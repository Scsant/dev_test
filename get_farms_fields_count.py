#!/usr/bin/env python3
"""
Script para buscar a quantidade de campos de TODAS as fazendas
e salvar em JSON com estatísticas
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
SCOPES = "ag1 ag2 org1 eq1 offline_access"

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

def load_farms_data():
    """
    Carrega os dados das fazendas do arquivo JSON
    """
    farms_file = f"farms_organization_{ORG_ID}.json"
    if not os.path.exists(farms_file):
        print(f"❌ Arquivo {farms_file} não encontrado. Execute get_all_farms.py primeiro.")
        return None
    
    with open(farms_file, 'r', encoding='utf-8') as f:
        return json.load(f)

def get_farm_fields_count(farm_id: str, farm_name: str) -> Optional[Dict[str, Any]]:
    """
    Busca a quantidade de campos de uma fazenda específica
    """
    tokens = get_valid_tokens()
    if not tokens:
        return None
    
    access_token = tokens.get('access_token')
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Accept': 'application/vnd.deere.axiom.v3+json'
    }
    
    fields_url = f"{API_BASE_URL}/organizations/{ORG_ID}/farms/{farm_id}/fields"
    
    try:
        response = requests.get(fields_url, headers=headers)
        if response.status_code == 200:
            data = response.json()
            total_fields = data.get('total', 0)
            
            return {
                'farm_id': farm_id,
                'farm_name': farm_name,
                'total_fields': total_fields,
                'status': 'success'
            }
        else:
            print(f"❌ Erro ao buscar campos da fazenda {farm_name}: {response.status_code}")
            return {
                'farm_id': farm_id,
                'farm_name': farm_name,
                'total_fields': 0,
                'status': f'error_{response.status_code}'
            }
    except Exception as e:
        print(f"❌ Erro na requisição para fazenda {farm_name}: {e}")
        return {
            'farm_id': farm_id,
            'farm_name': farm_name,
            'total_fields': 0,
            'status': f'error_{str(e)}'
        }

def analyze_farms_fields_distribution(farms_fields_data: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Analisa a distribuição de campos por fazenda
    """
    successful_farms = [f for f in farms_fields_data if f.get('status') == 'success']
    error_farms = [f for f in farms_fields_data if f.get('status') != 'success']
    
    if not successful_farms:
        return {
            'summary': 'Nenhuma fazenda processada com sucesso',
            'total_farms': len(farms_fields_data),
            'successful_farms': 0,
            'error_farms': len(error_farms)
        }
    
    # Estatísticas dos campos
    fields_counts = [f['total_fields'] for f in successful_farms]
    total_fields = sum(fields_counts)
    
    # Fazendas por faixa de campos
    farms_by_range = {
        '1-5 campos': len([f for f in fields_counts if 1 <= f <= 5]),
        '6-10 campos': len([f for f in fields_counts if 6 <= f <= 10]),
        '11-20 campos': len([f for f in fields_counts if 11 <= f <= 20]),
        '21-50 campos': len([f for f in fields_counts if 21 <= f <= 50]),
        '50+ campos': len([f for f in fields_counts if f > 50])
    }
    
    # Top 10 fazendas com mais campos
    top_farms = sorted(successful_farms, key=lambda x: x['total_fields'], reverse=True)[:10]
    
    # Fazendas sem campos
    farms_without_fields = [f for f in successful_farms if f['total_fields'] == 0]
    
    return {
        'summary': {
            'total_farms_processed': len(farms_fields_data),
            'successful_farms': len(successful_farms),
            'error_farms': len(error_farms),
            'total_fields': total_fields,
            'average_fields_per_farm': round(total_fields / len(successful_farms), 2) if successful_farms else 0,
            'min_fields': min(fields_counts) if fields_counts else 0,
            'max_fields': max(fields_counts) if fields_counts else 0
        },
        'distribution': farms_by_range,
        'top_10_farms_by_fields': [
            {
                'rank': i + 1,
                'farm_name': farm['farm_name'],
                'farm_id': farm['farm_id'],
                'total_fields': farm['total_fields']
            }
            for i, farm in enumerate(top_farms)
        ],
        'farms_without_fields': len(farms_without_fields),
        'farms_without_fields_list': [
            {
                'farm_name': farm['farm_name'],
                'farm_id': farm['farm_id']
            }
            for farm in farms_without_fields
        ]
    }

def main():
    """
    Função principal
    """
    print("🚀 Iniciando análise de campos por fazenda...")
    
    # Carregar dados das fazendas
    farms_data = load_farms_data()
    if not farms_data:
        return
    
    print(f"📋 Processando {len(farms_data)} fazendas...")
    
    # Lista para armazenar resultados
    farms_fields_data = []
    
    # Processar cada fazenda
    for i, farm in enumerate(farms_data, 1):
        farm_id = farm.get('id')
        farm_name = farm.get('name', 'N/A')
        
        print(f"🔍 [{i:3d}/{len(farms_data)}] Processando: {farm_name}")
        
        # Buscar quantidade de campos
        result = get_farm_fields_count(farm_id, farm_name)
        if result:
            farms_fields_data.append(result)
            
            # Mostrar progresso
            if result['status'] == 'success':
                print(f"   ✅ {result['total_fields']} campos")
            else:
                print(f"   ❌ Erro: {result['status']}")
        
        # Pequena pausa para não sobrecarregar a API
        time.sleep(0.1)
    
    # Salvar dados brutos
    output_file = f"farms_fields_count_{ORG_ID}.json"
    print(f"\n💾 Salvando dados em {output_file}...")
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump({
            'organization_id': ORG_ID,
            'generated_at': time.strftime('%Y-%m-%d %H:%M:%S'),
            'farms_data': farms_fields_data
        }, f, ensure_ascii=False, indent=2)
    
    # Analisar distribuição
    print("\n📊 Analisando distribuição...")
    analysis = analyze_farms_fields_distribution(farms_fields_data)
    
    # Salvar análise
    analysis_file = f"farms_fields_analysis_{ORG_ID}.json"
    print(f"💾 Salvando análise em {analysis_file}...")
    
    with open(analysis_file, 'w', encoding='utf-8') as f:
        json.dump(analysis, f, ensure_ascii=False, indent=2)
    
    # Exibir resumo
    print("\n" + "="*80)
    print("📊 RESUMO DA ANÁLISE DE CAMPOS POR FAZENDA")
    print("="*80)
    
    summary = analysis['summary']
    print(f"\n📈 Estatísticas Gerais:")
    print(f"   • Fazendas processadas: {summary['total_farms_processed']}")
    print(f"   • Fazendas com sucesso: {summary['successful_farms']}")
    print(f"   • Fazendas com erro: {summary['error_farms']}")
    print(f"   • Total de campos: {summary['total_fields']:,}")
    print(f"   • Média de campos por fazenda: {summary['average_fields_per_farm']}")
    print(f"   • Mínimo de campos: {summary['min_fields']}")
    print(f"   • Máximo de campos: {summary['max_fields']}")
    
    print(f"\n📊 Distribuição por Faixa:")
    for range_name, count in analysis['distribution'].items():
        print(f"   • {range_name}: {count} fazendas")
    
    print(f"\n🏆 Top 5 Fazendas com Mais Campos:")
    for farm in analysis['top_10_farms_by_fields'][:5]:
        print(f"   {farm['rank']}. {farm['farm_name']}: {farm['total_fields']} campos")
    
    print(f"\n⚠️  Fazendas sem campos: {analysis['farms_without_fields']}")
    
    print(f"\n✅ Análise completa! Arquivos gerados:")
    print(f"   • {output_file} - Dados brutos")
    print(f"   • {analysis_file} - Análise e estatísticas")

if __name__ == "__main__":
    main() 