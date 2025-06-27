#!/usr/bin/env python3
"""
Script para buscar e exibir dados de operações de campo da John Deere
"""

import os
import json
import requests
import time
from typing import Dict, List, Any
from jd import access_token, ensure_token_valid, API_BASE_URL

API_BASE_URL = "https://sandboxapi.deere.com/platform"
TOKEN_URL = "https://signin.johndeere.com/oauth2/aus78tnlaysMraFhC1t7/v1/token"
CLIENT_ID = "0oap8bfnk7ViKFk7M5d7"
CLIENT_SECRET = "usklX-2OR8SHRY9pziQ-uMS3qzxkwYR_ZpFatiuQtFPaWVi6NrmhZW9RQvFjVYlL"
REDIRECT_URI = "http://localhost:9090/callback"
SCOPES = "ag1 org1 eq1 offline_access"

def load_tokens():
    if os.path.exists('tokens.json'):
        with open('tokens.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data
    else:
        print("tokens.json não encontrado. Execute jd.py para autenticar.")
        return None

def save_tokens(tokens):
    with open('tokens.json', 'w', encoding='utf-8') as f:
        json.dump(tokens, f)
    print("Tokens atualizados em tokens.json.")

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
        print("❌ Refresh Token não disponível. Reautentique-se pelo jd.py.")
        return None
    print("🔄 Renovando access token via refresh token...")
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
        print("✅ Access token renovado com sucesso!")
        return tokens
    except requests.exceptions.RequestException as e:
        print(f"❌ Erro ao renovar access token: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"📄 Resposta de erro: {e.response.text}")
        return None

def get_valid_tokens():
    tokens = load_tokens()
    if not tokens:
        exit(1)
    if is_token_expired_or_expiring(tokens):
        tokens = refresh_access_token(tokens)
        if not tokens:
            print("❌ Não foi possível renovar o token. Execute jd.py para reautenticar.")
            exit(1)
    return tokens

def get_field_operations(organization_id: str) -> Dict[str, Any]:
    """
    Busca operações de campo para uma organização específica
    """
    tokens = get_valid_tokens()
    access_token = tokens.get('access_token')
    print(f"🔍 Buscando operações de campo para organização {organization_id}...")
    
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Accept': 'application/vnd.deere.axiom.v3+json'
    }
    
    # URL do endpoint de operações de campo
    field_ops_url = f"{API_BASE_URL}/organizations/{organization_id}/fieldOperations"
    
    try:
        print(f"📡 Fazendo requisição para: {field_ops_url}")
        response = requests.get(field_ops_url, headers=headers)
        
        print(f"📊 Status da resposta: {response.status_code}")
        print(f"📋 Headers da resposta: {dict(response.headers)}")
        
        response.raise_for_status()
        field_operations = response.json()
        
        print("✅ Operações de campo obtidas com sucesso!")
        return field_operations
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Erro ao buscar operações de campo: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"📊 Status de erro: {e.response.status_code}")
            print(f"📄 Resposta de erro: {e.response.text}")
        return None

def analyze_field_operations(field_ops_data: Dict[str, Any]) -> None:
    """
    Analisa e exibe informações das operações de campo de forma organizada
    """
    print("\n" + "="*80)
    print("🌾 ANÁLISE DAS OPERAÇÕES DE CAMPO")
    print("="*80)
    
    if not field_ops_data:
        print("❌ Nenhum dado de operações de campo para analisar.")
        return
    
    # Informações gerais
    total_ops = field_ops_data.get('total', 0)
    print(f"\n📈 Total de operações de campo: {total_ops}")
    
    # Links da resposta principal
    main_links = field_ops_data.get('links', [])
    if main_links:
        print(f"\n🔗 Links principais:")
        for link in main_links:
            print(f"   • {link.get('rel', 'N/A')}: {link.get('uri', 'N/A')}")
    
    # Processar cada operação
    operations = field_ops_data.get('values', [])
    
    if not operations:
        print("\n📭 Nenhuma operação de campo encontrada.")
        return
    
    for i, operation in enumerate(operations, 1):
        print(f"\n{'='*60}")
        print(f"🌾 OPERAÇÃO {i}/{len(operations)}")
        print(f"{'='*60}")
        
        # Informações básicas da operação
        op_id = operation.get('id', 'N/A')
        op_name = operation.get('name', 'N/A')
        op_type = operation.get('type', 'N/A')
        op_status = operation.get('status', 'N/A')
        
        print(f"📋 Informações Básicas:")
        print(f"   • ID: {op_id}")
        print(f"   • Nome: {op_name}")
        print(f"   • Tipo: {op_type}")
        print(f"   • Status: {op_status}")
        
        # Informações de data/hora
        start_date = operation.get('startDate', 'N/A')
        end_date = operation.get('endDate', 'N/A')
        created_date = operation.get('createdDate', 'N/A')
        modified_date = operation.get('modifiedDate', 'N/A')
        
        print(f"\n📅 Informações de Data/Hora:")
        print(f"   • Data de início: {start_date}")
        print(f"   • Data de fim: {end_date}")
        print(f"   • Data de criação: {created_date}")
        print(f"   • Data de modificação: {modified_date}")
        
        # Informações de campo
        field_info = operation.get('field', {})
        if field_info:
            field_id = field_info.get('id', 'N/A')
            field_name = field_info.get('name', 'N/A')
            print(f"\n🌱 Informações do Campo:")
            print(f"   • ID do campo: {field_id}")
            print(f"   • Nome do campo: {field_name}")
        
        # Informações de máquina
        machine_info = operation.get('machine', {})
        if machine_info:
            machine_id = machine_info.get('id', 'N/A')
            machine_name = machine_info.get('name', 'N/A')
            print(f"\n🚜 Informações da Máquina:")
            print(f"   • ID da máquina: {machine_id}")
            print(f"   • Nome da máquina: {machine_name}")
        
        # Informações de produto
        product_info = operation.get('product', {})
        if product_info:
            product_id = product_info.get('id', 'N/A')
            product_name = product_info.get('name', 'N/A')
            print(f"\n🧪 Informações do Produto:")
            print(f"   • ID do produto: {product_id}")
            print(f"   • Nome do produto: {product_name}")
        
        # Métricas
        metrics = operation.get('metrics', {})
        if metrics:
            print(f"\n📊 Métricas:")
            for key, value in metrics.items():
                print(f"   • {key}: {value}")
        
        # Links disponíveis
        links = operation.get('links', [])
        if links:
            print(f"\n🔗 Endpoints disponíveis ({len(links)} total):")
            for link in links:
                rel = link.get('rel', 'N/A')
                uri = link.get('uri', 'N/A')
                print(f"   • {rel}: {uri}")

def print_field_operations_summary(field_ops_data: Dict[str, Any]) -> None:
    """
    Imprime um resumo das operações de campo
    """
    if not field_ops_data:
        return
        
    operations = field_ops_data.get('values', [])
    if not operations:
        return
    
    print(f"\n{'='*80}")
    print("📋 RESUMO DAS OPERAÇÕES DE CAMPO")
    print(f"{'='*80}")
    
    print(f"\n📊 Total de operações: {len(operations)}")
    
    # Agrupar por tipo
    types_count = {}
    status_count = {}
    
    for op in operations:
        op_type = op.get('type', 'Desconhecido')
        op_status = op.get('status', 'Desconhecido')
        
        types_count[op_type] = types_count.get(op_type, 0) + 1
        status_count[op_status] = status_count.get(op_status, 0) + 1
    
    print(f"\n📈 Operações por tipo:")
    for op_type, count in types_count.items():
        print(f"   • {op_type}: {count}")
    
    print(f"\n📊 Operações por status:")
    for status, count in status_count.items():
        print(f"   • {status}: {count}")

def main():
    """
    Função principal
    """
    # ID da organização BSPF - 2025
    organization_id = "5881930"
    
    print("🚀 Iniciando busca de operações de campo...")
    
    # Buscar operações de campo
    field_ops_data = get_field_operations(organization_id)
    
    if field_ops_data:
        # Exibir dados brutos (opcional)
        print(f"\n📄 Dados brutos da resposta:")
        print(json.dumps(field_ops_data, indent=2))
        
        # Análise detalhada
        analyze_field_operations(field_ops_data)
        
        # Resumo
        print_field_operations_summary(field_ops_data)
        
        print(f"\n✅ Análise concluída!")
    else:
        print("❌ Falha ao obter operações de campo.")

if __name__ == "__main__":
    main() 