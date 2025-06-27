#!/usr/bin/env python3
"""
Script para buscar Map Layer Summaries dos campos
Endpoint: /organizations/{orgId}/fields/{fieldId}/mapLayerSummaries
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

def get_map_layer_summaries(
    organization_id: str,
    field_id: str,
    include_partial_summaries: bool = False,
    embed: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    """
    Busca Map Layer Summaries de um campo específico
    
    Args:
        organization_id: ID da organização
        field_id: ID do campo
        include_partial_summaries: Incluir resumos parciais (sem recursos de arquivo)
        embed: Valores para embed (ex: 'mapLayers')
    """
    tokens = get_valid_tokens()
    if not tokens:
        return None
    
    access_token = tokens.get('access_token')
    
    print(f"🗺️ Buscando Map Layer Summaries...")
    print(f"   • Organização: {organization_id}")
    print(f"   • Campo: {field_id}")
    
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Accept': 'application/vnd.deere.axiom.v3+json'
    }
    
    # URL do endpoint
    map_layers_url = f"{API_BASE_URL}/organizations/{organization_id}/fields/{field_id}/mapLayerSummaries"
    
    # Parâmetros de query
    params = {}
    if include_partial_summaries:
        params['includePartialSummaries'] = 'true'
    if embed:
        params['embed'] = embed
    
    try:
        print(f"📡 Fazendo requisição para: {map_layers_url}")
        if params:
            print(f"📋 Parâmetros: {params}")
        
        response = requests.get(map_layers_url, headers=headers, params=params)
        
        print(f"📊 Status da resposta: {response.status_code}")
        print(f"📋 Headers da resposta: {dict(response.headers)}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Map Layer Summaries obtidos com sucesso!")
            return data
        else:
            print(f"❌ Erro {response.status_code}: {response.text}")
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Erro na requisição: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"📊 Status de erro: {e.response.status_code}")
            print(f"📄 Resposta de erro: {e.response.text}")
        return None

def analyze_map_layer_summaries(map_layers_data: Dict[str, Any]) -> None:
    """
    Analisa e exibe informações dos Map Layer Summaries
    """
    print("\n" + "="*80)
    print("🗺️ ANÁLISE DOS MAP LAYER SUMMARIES")
    print("="*80)
    
    if not map_layers_data:
        print("❌ Nenhum dado de Map Layer Summaries para analisar.")
        return
    
    # Informações gerais
    total_summaries = map_layers_data.get('total', 0)
    print(f"\n📈 Total de Map Layer Summaries: {total_summaries}")
    
    # Links da resposta principal
    main_links = map_layers_data.get('links', [])
    if main_links:
        print(f"\n🔗 Links principais:")
        for link in main_links:
            print(f"   • {link.get('rel', 'N/A')}: {link.get('uri', 'N/A')}")
    
    # Processar cada Map Layer Summary
    summaries = map_layers_data.get('values', [])
    
    if not summaries:
        print("\n📭 Nenhum Map Layer Summary encontrado.")
        return
    
    print(f"\n📋 Map Layer Summaries disponíveis:")
    
    for i, summary in enumerate(summaries, 1):
        print(f"\n{'='*60}")
        print(f"🗺️ MAP LAYER SUMMARY {i}/{len(summaries)}")
        print(f"{'='*60}")
        
        # Informações básicas
        summary_id = summary.get('id', 'N/A')
        summary_type = summary.get('@type', 'N/A')
        name = summary.get('name', 'N/A')
        description = summary.get('description', 'N/A')
        
        print(f"📋 Informações Básicas:")
        print(f"   • ID: {summary_id}")
        print(f"   • Tipo: {summary_type}")
        print(f"   • Nome: {name}")
        print(f"   • Descrição: {description}")
        
        # Informações de data/hora
        created_time = summary.get('createdTime', 'N/A')
        modified_time = summary.get('modifiedTime', 'N/A')
        
        print(f"\n📅 Informações de Data/Hora:")
        print(f"   • Criado em: {created_time}")
        print(f"   • Modificado em: {modified_time}")
        
        # Informações de arquivo
        file_resources = summary.get('fileResources', [])
        if file_resources:
            print(f"\n📁 Recursos de Arquivo ({len(file_resources)} total):")
            for file_resource in file_resources:
                file_id = file_resource.get('id', 'N/A')
                file_name = file_resource.get('name', 'N/A')
                file_size = file_resource.get('size', 'N/A')
                file_type = file_resource.get('contentType', 'N/A')
                
                print(f"   • Arquivo: {file_name}")
                print(f"     - ID: {file_id}")
                print(f"     - Tamanho: {file_size} bytes")
                print(f"     - Tipo: {file_type}")
                
                # Links do arquivo
                file_links = file_resource.get('links', [])
                if file_links:
                    print(f"     - Links disponíveis:")
                    for link in file_links:
                        rel = link.get('rel', 'N/A')
                        uri = link.get('uri', 'N/A')
                        print(f"       * {rel}: {uri}")
        
        # Map Layers (se embed=mapLayers foi usado)
        map_layers = summary.get('mapLayers', [])
        if map_layers:
            print(f"\n🗺️ Map Layers ({len(map_layers)} total):")
            for map_layer in map_layers:
                layer_id = map_layer.get('id', 'N/A')
                layer_name = map_layer.get('name', 'N/A')
                layer_type = map_layer.get('mapLayerType', 'N/A')
                
                print(f"   • Layer: {layer_name}")
                print(f"     - ID: {layer_id}")
                print(f"     - Tipo: {layer_type}")
        
        # Links disponíveis
        links = summary.get('links', [])
        if links:
            print(f"\n🔗 Endpoints disponíveis ({len(links)} total):")
            for link in links:
                rel = link.get('rel', 'N/A')
                uri = link.get('uri', 'N/A')
                print(f"   • {rel}: {uri}")

def test_multiple_fields():
    """
    Testa o endpoint em múltiplos campos para verificar quais têm dados
    """
    organization_id = "5881930"
    
    # Lista de campos para testar (usando alguns IDs do arquivo JSON)
    test_fields = [
        {
            'id': '19f73266-741a-99e1-3c04-a513c7481e3f',
            'name': '0001 - 001'
        },
        {
            'id': '5527ba3d-ea00-c761-3436-8b0e98b24a1f',
            'name': '2439 - 001-01'
        },
        {
            'id': 'a7848fbf-3402-dd49-c2d6-b98995fc0e68',
            'name': '0001 - 002'
        }
    ]
    
    print("🧪 Testando Map Layer Summaries em múltiplos campos...")
    
    for field in test_fields:
        print(f"\n{'='*80}")
        print(f"🌾 TESTANDO CAMPO: {field['name']} (ID: {field['id']})")
        print(f"{'='*80}")
        
        # Teste 1: Sem parâmetros especiais
        print(f"\n📋 Teste 1: Busca básica")
        map_data = get_map_layer_summaries(
            organization_id=organization_id,
            field_id=field['id']
        )
        
        if map_data:
            analyze_map_layer_summaries(map_data)
            
            # Teste 2: Com embed=mapLayers
            print(f"\n📋 Teste 2: Com embed=mapLayers")
            map_data_with_embed = get_map_layer_summaries(
                organization_id=organization_id,
                field_id=field['id'],
                embed='mapLayers'
            )
            
            if map_data_with_embed:
                analyze_map_layer_summaries(map_data_with_embed)
        else:
            print("❌ Nenhum dado encontrado para este campo.")

def main():
    """
    Função principal
    """
    print("🚀 Iniciando busca de Map Layer Summaries...")
    
    # Testar em múltiplos campos
    test_multiple_fields()
    
    print(f"\n✅ Análise completa concluída!")

if __name__ == "__main__":
    main() 