#!/usr/bin/env python3
"""
Script para buscar Boundaries (limites) dos campos
Endpoint: /organizations/{orgId}/fields/{fieldId}/boundaries
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

def get_field_boundaries(
    organization_id: str,
    field_id: str,
    simple: bool = False,
    accuracy_data: bool = False
) -> Optional[Dict[str, Any]]:
    """
    Busca boundaries (limites) de um campo específico
    
    Args:
        organization_id: ID da organização
        field_id: ID do campo
        simple: Se True, retorna limites simplificados
        accuracy_data: Se True, inclui dados de precisão
    """
    tokens = get_valid_tokens()
    if not tokens:
        return None
    
    access_token = tokens.get('access_token')
    
    print(f"🗺️ Buscando Boundaries do campo...")
    print(f"   • Organização: {organization_id}")
    print(f"   • Campo: {field_id}")
    
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Accept': 'application/vnd.deere.axiom.v3+json'
    }
    
    # URL base do endpoint
    boundaries_url = f"{API_BASE_URL}/organizations/{organization_id}/fields/{field_id}/boundaries"
    
    # Parâmetros de query
    params = {}
    if simple:
        params['simple'] = 'true'
    if accuracy_data:
        params['accuracyData'] = 'true'
    
    try:
        print(f"📡 Fazendo requisição para: {boundaries_url}")
        if params:
            print(f"📋 Parâmetros: {params}")
        
        response = requests.get(boundaries_url, headers=headers, params=params)
        
        print(f"📊 Status da resposta: {response.status_code}")
        print(f"📋 Headers da resposta: {dict(response.headers)}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Boundaries obtidos com sucesso!")
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

def analyze_boundaries(boundaries_data: Dict[str, Any]) -> None:
    """
    Analisa e exibe informações dos boundaries
    """
    print("\n" + "="*80)
    print("🗺️ ANÁLISE DOS BOUNDARIES (LIMITES)")
    print("="*80)
    
    if not boundaries_data:
        print("❌ Nenhum dado de boundaries para analisar.")
        return
    
    # Informações gerais
    total_boundaries = boundaries_data.get('total', 0)
    print(f"\n📈 Total de boundaries: {total_boundaries}")
    
    # Links da resposta principal
    main_links = boundaries_data.get('links', [])
    if main_links:
        print(f"\n🔗 Links principais:")
        for link in main_links:
            print(f"   • {link.get('rel', 'N/A')}: {link.get('uri', 'N/A')}")
    
    # Processar cada boundary
    boundaries = boundaries_data.get('values', [])
    
    if not boundaries:
        print("\n📭 Nenhum boundary encontrado.")
        return
    
    print(f"\n📋 Boundaries disponíveis:")
    
    for i, boundary in enumerate(boundaries, 1):
        print(f"\n{'='*60}")
        print(f"🗺️ BOUNDARY {i}/{len(boundaries)}")
        print(f"{'='*60}")
        
        # Informações básicas
        boundary_id = boundary.get('id', 'N/A')
        boundary_type = boundary.get('@type', 'N/A')
        name = boundary.get('name', 'N/A')
        description = boundary.get('description', 'N/A')
        
        print(f"📋 Informações Básicas:")
        print(f"   • ID: {boundary_id}")
        print(f"   • Tipo: {boundary_type}")
        print(f"   • Nome: {name}")
        print(f"   • Descrição: {description}")
        
        # Informações de data/hora
        created_time = boundary.get('createdTime', 'N/A')
        modified_time = boundary.get('modifiedTime', 'N/A')
        
        print(f"\n📅 Informações de Data/Hora:")
        print(f"   • Criado em: {created_time}")
        print(f"   • Modificado em: {modified_time}")
        
        # Informações de área
        area = boundary.get('area')
        if area:
            area_value = area.get('value', 'N/A')
            area_unit = area.get('unitId', 'N/A')
            print(f"\n📏 Informações de Área:")
            print(f"   • Área: {area_value} {area_unit}")
        
        # Informações de perímetro
        perimeter = boundary.get('perimeter')
        if perimeter:
            perimeter_value = perimeter.get('value', 'N/A')
            perimeter_unit = perimeter.get('unitId', 'N/A')
            print(f"   • Perímetro: {perimeter_value} {perimeter_unit}")
        
        # Informações de precisão
        accuracy = boundary.get('accuracy')
        if accuracy:
            accuracy_value = accuracy.get('value', 'N/A')
            accuracy_unit = accuracy.get('unitId', 'N/A')
            print(f"   • Precisão: {accuracy_value} {accuracy_unit}")
        
        # Coordenadas (se disponíveis)
        coordinates = boundary.get('coordinates')
        if coordinates:
            print(f"\n📍 Coordenadas:")
            print(f"   • Total de pontos: {len(coordinates)}")
            if len(coordinates) > 0:
                print(f"   • Primeiro ponto: {coordinates[0]}")
                if len(coordinates) > 1:
                    print(f"   • Último ponto: {coordinates[-1]}")
        
        # Informações de arquivo
        file_resources = boundary.get('fileResources', [])
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
        
        # Links disponíveis
        links = boundary.get('links', [])
        if links:
            print(f"\n🔗 Endpoints disponíveis ({len(links)} total):")
            for link in links:
                rel = link.get('rel', 'N/A')
                uri = link.get('uri', 'N/A')
                print(f"   • {rel}: {uri}")

def test_multiple_boundary_types():
    """
    Testa diferentes tipos de boundaries para um campo
    """
    organization_id = "5881930"
    field_id = "19f73266-741a-99e1-3c04-a513c7481e3f"  # Campo 0001 - 001
    
    print("🧪 Testando diferentes tipos de boundaries...")
    
    # Teste 1: Boundaries normais
    print(f"\n{'='*80}")
    print(f"🗺️ TESTE 1: Boundaries normais")
    print(f"{'='*80}")
    
    boundaries_data = get_field_boundaries(
        organization_id=organization_id,
        field_id=field_id
    )
    
    if boundaries_data:
        analyze_boundaries(boundaries_data)
        
        # Teste 2: Boundaries simplificados
        print(f"\n{'='*80}")
        print(f"🗺️ TESTE 2: Boundaries simplificados")
        print(f"{'='*80}")
        
        simple_boundaries = get_field_boundaries(
            organization_id=organization_id,
            field_id=field_id,
            simple=True
        )
        
        if simple_boundaries:
            analyze_boundaries(simple_boundaries)
        
        # Teste 3: Boundaries com dados de precisão
        print(f"\n{'='*80}")
        print(f"🗺️ TESTE 3: Boundaries com dados de precisão")
        print(f"{'='*80}")
        
        accuracy_boundaries = get_field_boundaries(
            organization_id=organization_id,
            field_id=field_id,
            accuracy_data=True
        )
        
        if accuracy_boundaries:
            analyze_boundaries(accuracy_boundaries)
    else:
        print("❌ Nenhum boundary encontrado para este campo.")

def test_multiple_fields():
    """
    Testa boundaries em múltiplos campos
    """
    organization_id = "5881930"
    
    # Lista de campos para testar
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
    
    print("🧪 Testando boundaries em múltiplos campos...")
    
    for field in test_fields:
        print(f"\n{'='*80}")
        print(f"🌾 TESTANDO CAMPO: {field['name']} (ID: {field['id']})")
        print(f"{'='*80}")
        
        boundaries_data = get_field_boundaries(
            organization_id=organization_id,
            field_id=field['id']
        )
        
        if boundaries_data:
            analyze_boundaries(boundaries_data)
        else:
            print("❌ Nenhum boundary encontrado para este campo.")

def main():
    """
    Função principal
    """
    print("🚀 Iniciando busca de Boundaries...")
    
    # Testar diferentes tipos de boundaries
    test_multiple_boundary_types()
    
    print(f"\n{'='*80}")
    print("🧪 TESTE ADICIONAL: Múltiplos campos")
    print(f"{'='*80}")
    
    # Testar em múltiplos campos
    test_multiple_fields()
    
    print(f"\n✅ Análise completa concluída!")

if __name__ == "__main__":
    main() 