#!/usr/bin/env python3
"""
Script para buscar TODAS as fazendas da organização
Endpoint: /organizations/{orgId}/farms
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
ITEM_LIMIT = 100  # Máximo permitido pela API

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

def fetch_all_farms():
    """
    Busca TODAS as fazendas da organização (paginado)
    """
    tokens = get_valid_tokens()
    if not tokens:
        return
    
    access_token = tokens.get('access_token')
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Accept': 'application/vnd.deere.axiom.v3+json'
    }
    
    all_farms: List[Dict[str, Any]] = []
    page_offset = 0
    total = None
    
    print(f"🔄 Buscando TODAS as fazendas da organização {ORG_ID}...")
    
    while True:
        url = f"{API_BASE_URL}/organizations/{ORG_ID}/farms?pageOffset={page_offset}&itemLimit={ITEM_LIMIT}"
        print(f"📡 Requisitando: {url}")
        
        response = requests.get(url, headers=headers)
        print(f"📊 Status: {response.status_code}")
        
        if response.status_code != 200:
            print(f"❌ Erro ao buscar fazendas: {response.status_code} - {response.text}")
            break
        
        data = response.json()
        
        if total is None:
            total = data.get('total', None)
            print(f"📈 Total de fazendas: {total}")
        
        values = data.get('values', [])
        print(f"➕ Adicionando {len(values)} fazendas (página offset {page_offset})")
        all_farms.extend(values)
        
        # Verifica se há próxima página
        links = data.get('links', [])
        next_page_link = next((l for l in links if l.get('rel') == 'nextPage'), None)
        
        if next_page_link:
            # Extrai o próximo pageOffset da URL
            next_url = next_page_link['uri']
            from urllib.parse import urlparse, parse_qs
            qs = parse_qs(urlparse(next_url).query)
            page_offset = int(qs.get('pageOffset', [page_offset + ITEM_LIMIT])[0])
        else:
            print("✅ Todas as páginas baixadas.")
            break
    
    print(f"💾 Salvando {len(all_farms)} fazendas em farms_organization_{ORG_ID}.json...")
    with open(f"farms_organization_{ORG_ID}.json", "w", encoding="utf-8") as f:
        json.dump(all_farms, f, ensure_ascii=False, indent=2)
    
    print("🎉 Download completo!")
    return all_farms

def analyze_farms_summary(farms_data: List[Dict[str, Any]]) -> None:
    """
    Analisa e exibe um resumo das fazendas
    """
    print("\n" + "="*80)
    print("🏡 RESUMO DAS FAZENDAS DA ORGANIZAÇÃO")
    print("="*80)
    
    if not farms_data:
        print("❌ Nenhuma fazenda encontrada.")
        return
    
    print(f"\n📈 Total de fazendas encontradas: {len(farms_data)}")
    
    # Contadores
    archived_count = 0
    active_count = 0
    
    # Lista de fazendas
    print(f"\n📋 Lista de todas as fazendas:")
    
    for i, farm in enumerate(farms_data, 1):
        farm_id = farm.get('id', 'N/A')
        name = farm.get('name', 'N/A')
        archived = farm.get('archived', False)
        
        if archived:
            archived_count += 1
            status = "📦 ARQUIVADA"
        else:
            active_count += 1
            status = "✅ ATIVA"
        
        print(f"   {i:3d}. {name} (ID: {farm_id}) - {status}")
    
    print(f"\n📊 Estatísticas:")
    print(f"   • Fazendas ativas: {active_count}")
    print(f"   • Fazendas arquivadas: {archived_count}")
    print(f"   • Total: {len(farms_data)}")

def get_farm_details(farm_id: str) -> Optional[Dict[str, Any]]:
    """
    Busca detalhes de uma fazenda específica
    """
    tokens = get_valid_tokens()
    if not tokens:
        return None
    
    access_token = tokens.get('access_token')
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Accept': 'application/vnd.deere.axiom.v3+json'
    }
    
    farm_url = f"{API_BASE_URL}/organizations/{ORG_ID}/farms/{farm_id}"
    
    try:
        response = requests.get(farm_url, headers=headers)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"❌ Erro ao buscar detalhes da fazenda: {response.status_code}")
            return None
    except Exception as e:
        print(f"❌ Erro na requisição: {e}")
        return None

def get_farm_fields(farm_id: str) -> Optional[Dict[str, Any]]:
    """
    Busca todos os campos de uma fazenda específica
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
            return response.json()
        else:
            print(f"❌ Erro ao buscar campos da fazenda: {response.status_code}")
            return None
    except Exception as e:
        print(f"❌ Erro na requisição: {e}")
        return None

def analyze_farm_with_fields(farm_data: Dict[str, Any], fields_data: Optional[Dict[str, Any]]) -> None:
    """
    Analisa uma fazenda com seus campos
    """
    farm_id = farm_data.get('id', 'N/A')
    farm_name = farm_data.get('name', 'N/A')
    archived = farm_data.get('archived', False)
    
    print(f"\n{'='*60}")
    print(f"🏡 FAZENDA: {farm_name}")
    print(f"{'='*60}")
    print(f"📋 ID: {farm_id}")
    print(f"📦 Status: {'Arquivada' if archived else 'Ativa'}")
    
    if fields_data:
        total_fields = fields_data.get('total', 0)
        fields = fields_data.get('values', [])
        
        print(f"🌾 Total de campos: {total_fields}")
        
        if fields:
            print(f"📋 Campos desta fazenda:")
            for i, field in enumerate(fields[:10], 1):  # Mostra apenas os primeiros 10
                field_name = field.get('name', 'N/A')
                field_id = field.get('id', 'N/A')
                field_archived = field.get('archived', False)
                
                status = "📦" if field_archived else "✅"
                print(f"   {i:2d}. {field_name} (ID: {field_id}) {status}")
            
            if len(fields) > 10:
                print(f"   ... e mais {len(fields) - 10} campos")
    else:
        print("❌ Não foi possível obter os campos desta fazenda")

def main():
    """
    Função principal
    """
    print("🚀 Iniciando busca de TODAS as fazendas...")
    
    # Buscar todas as fazendas
    farms_data = fetch_all_farms()
    
    if farms_data:
        # Analisar resumo
        analyze_farms_summary(farms_data)
        
        # Analisar algumas fazendas em detalhes
        print(f"\n{'='*80}")
        print("🔍 ANÁLISE DETALHADA DE ALGUMAS FAZENDAS")
        print(f"{'='*80}")
        
        # Analisar as primeiras 3 fazendas ativas
        active_farms = [f for f in farms_data if not f.get('archived', False)]
        
        for i, farm in enumerate(active_farms[:3], 1):
            print(f"\n🔍 Analisando fazenda {i}/3...")
            
            # Buscar detalhes da fazenda
            farm_details = get_farm_details(farm.get('id'))
            
            # Buscar campos da fazenda
            farm_fields = get_farm_fields(farm.get('id'))
            
            # Analisar
            if farm_details:
                analyze_farm_with_fields(farm_details, farm_fields)
            else:
                print(f"❌ Não foi possível obter detalhes da fazenda {farm.get('name', 'N/A')}")
    
    print(f"\n✅ Análise completa concluída!")

if __name__ == "__main__":
    main() 