#!/usr/bin/env python3
"""
Script para buscar Farms e Clients dos campos
Endpoints: 
- /organizations/{orgId}/fields/{fieldId}/farms
- /organizations/{orgId}/fields/{fieldId}/clients
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

def get_field_farms(
    organization_id: str,
    field_id: str
) -> Optional[Dict[str, Any]]:
    """
    Busca fazendas associadas a um campo específico
    """
    tokens = get_valid_tokens()
    if not tokens:
        return None
    
    access_token = tokens.get('access_token')
    
    print(f"🏡 Buscando Farms do campo...")
    print(f"   • Organização: {organization_id}")
    print(f"   • Campo: {field_id}")
    
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Accept': 'application/vnd.deere.axiom.v3+json'
    }
    
    # URL do endpoint
    farms_url = f"{API_BASE_URL}/organizations/{organization_id}/fields/{field_id}/farms"
    
    try:
        print(f"📡 Fazendo requisição para: {farms_url}")
        
        response = requests.get(farms_url, headers=headers)
        
        print(f"📊 Status da resposta: {response.status_code}")
        print(f"📋 Headers da resposta: {dict(response.headers)}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Farms obtidos com sucesso!")
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

def get_field_clients(
    organization_id: str,
    field_id: str
) -> Optional[Dict[str, Any]]:
    """
    Busca clientes associados a um campo específico
    """
    tokens = get_valid_tokens()
    if not tokens:
        return None
    
    access_token = tokens.get('access_token')
    
    print(f"👥 Buscando Clients do campo...")
    print(f"   • Organização: {organization_id}")
    print(f"   • Campo: {field_id}")
    
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Accept': 'application/vnd.deere.axiom.v3+json'
    }
    
    # URL do endpoint
    clients_url = f"{API_BASE_URL}/organizations/{organization_id}/fields/{field_id}/clients"
    
    try:
        print(f"📡 Fazendo requisição para: {clients_url}")
        
        response = requests.get(clients_url, headers=headers)
        
        print(f"📊 Status da resposta: {response.status_code}")
        print(f"📋 Headers da resposta: {dict(response.headers)}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Clients obtidos com sucesso!")
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

def analyze_farms(farms_data: Dict[str, Any], organization_id: str) -> None:
    """
    Analisa e exibe informações das fazendas
    """
    print("\n" + "="*80)
    print("🏡 ANÁLISE DAS FAZENDAS")
    print("="*80)
    
    if not farms_data:
        print("❌ Nenhum dado de fazendas para analisar.")
        return
    
    # Informações gerais
    total_farms = farms_data.get('total', 0)
    print(f"\n📈 Total de fazendas: {total_farms}")
    
    # Links da resposta principal
    main_links = farms_data.get('links', [])
    if main_links:
        print(f"\n🔗 Links principais:")
        for link in main_links:
            print(f"   • {link.get('rel', 'N/A')}: {link.get('uri', 'N/A')}")
    
    # Processar cada fazenda
    farms = farms_data.get('values', [])
    
    if not farms:
        print("\n📭 Nenhuma fazenda encontrada.")
        return
    
    print(f"\n📋 Fazendas disponíveis:")
    
    for i, farm in enumerate(farms, 1):
        print(f"\n{'='*60}")
        print(f"🏡 FAZENDA {i}/{len(farms)}")
        print(f"{'='*60}")
        
        # Informações básicas
        farm_id = farm.get('id', 'N/A')
        farm_type = farm.get('@type', 'N/A')
        name = farm.get('name', 'N/A')
        description = farm.get('description', 'N/A')
        
        print(f"📋 Informações Básicas:")
        print(f"   • ID: {farm_id}")
        print(f"   • Tipo: {farm_type}")
        print(f"   • Nome: {name}")
        print(f"   • Descrição: {description}")
        
        # Informações de data/hora
        created_time = farm.get('createdTime', 'N/A')
        modified_time = farm.get('modifiedTime', 'N/A')
        
        print(f"\n📅 Informações de Data/Hora:")
        print(f"   • Criado em: {created_time}")
        print(f"   • Modificado em: {modified_time}")
        
        # Informações de endereço
        address = farm.get('address')
        if address:
            print(f"\n📍 Informações de Endereço:")
            street = address.get('street', 'N/A')
            city = address.get('city', 'N/A')
            state = address.get('state', 'N/A')
            postal_code = address.get('postalCode', 'N/A')
            country = address.get('country', 'N/A')
            
            print(f"   • Rua: {street}")
            print(f"   • Cidade: {city}")
            print(f"   • Estado: {state}")
            print(f"   • CEP: {postal_code}")
            print(f"   • País: {country}")
        
        # Links disponíveis
        links = farm.get('links', [])
        if links:
            print(f"\n🔗 Endpoints disponíveis ({len(links)} total):")
            for link in links:
                rel = link.get('rel', 'N/A')
                uri = link.get('uri', 'N/A')
                print(f"   • {rel}: {uri}")
        
        # Buscar informações detalhadas da fazenda
        print(f"\n🔍 Buscando informações detalhadas da fazenda...")
        farm_url = f"{API_BASE_URL}/organizations/{organization_id}/farms/{farm_id}"
        
        tokens = get_valid_tokens()
        if tokens:
            access_token = tokens.get('access_token')
            headers = {
                'Authorization': f'Bearer {access_token}',
                'Accept': 'application/vnd.deere.axiom.v3+json'
            }
            
            try:
                response = requests.get(farm_url, headers=headers)
                if response.status_code == 200:
                    farm_details = response.json()
                    print(f"✅ Informações detalhadas obtidas!")
                    
                    # Informações adicionais
                    archived = farm_details.get('archived', False)
                    print(f"   • Arquivado: {'✅ Sim' if archived else '❌ Não'}")
                    
                    # Informações de área (se disponível)
                    area = farm_details.get('area')
                    if area:
                        area_value = area.get('value', 'N/A')
                        area_unit = area.get('unitId', 'N/A')
                        print(f"   • Área total: {area_value} {area_unit}")
                    
                    # Links detalhados
                    detailed_links = farm_details.get('links', [])
                    if detailed_links:
                        print(f"   • Links detalhados ({len(detailed_links)} total):")
                        for link in detailed_links:
                            rel = link.get('rel', 'N/A')
                            uri = link.get('uri', 'N/A')
                            print(f"     - {rel}: {uri}")
                else:
                    print(f"❌ Erro ao buscar detalhes: {response.status_code}")
            except Exception as e:
                print(f"❌ Erro na requisição: {e}")

def analyze_clients(clients_data: Dict[str, Any], organization_id: str) -> None:
    """
    Analisa e exibe informações dos clientes
    """
    print("\n" + "="*80)
    print("👥 ANÁLISE DOS CLIENTES")
    print("="*80)
    
    if not clients_data:
        print("❌ Nenhum dado de clientes para analisar.")
        return
    
    # Informações gerais
    total_clients = clients_data.get('total', 0)
    print(f"\n📈 Total de clientes: {total_clients}")
    
    # Links da resposta principal
    main_links = clients_data.get('links', [])
    if main_links:
        print(f"\n🔗 Links principais:")
        for link in main_links:
            print(f"   • {link.get('rel', 'N/A')}: {link.get('uri', 'N/A')}")
    
    # Processar cada cliente
    clients = clients_data.get('values', [])
    
    if not clients:
        print("\n📭 Nenhum cliente encontrado.")
        return
    
    print(f"\n📋 Clientes disponíveis:")
    
    for i, client in enumerate(clients, 1):
        print(f"\n{'='*60}")
        print(f"👥 CLIENTE {i}/{len(clients)}")
        print(f"{'='*60}")
        
        # Informações básicas
        client_id = client.get('id', 'N/A')
        client_type = client.get('@type', 'N/A')
        name = client.get('name', 'N/A')
        description = client.get('description', 'N/A')
        
        print(f"📋 Informações Básicas:")
        print(f"   • ID: {client_id}")
        print(f"   • Tipo: {client_type}")
        print(f"   • Nome: {name}")
        print(f"   • Descrição: {description}")
        
        # Informações de data/hora
        created_time = client.get('createdTime', 'N/A')
        modified_time = client.get('modifiedTime', 'N/A')
        
        print(f"\n📅 Informações de Data/Hora:")
        print(f"   • Criado em: {created_time}")
        print(f"   • Modificado em: {modified_time}")
        
        # Informações de contato
        contact_info = client.get('contactInfo')
        if contact_info:
            print(f"\n📞 Informações de Contato:")
            email = contact_info.get('email', 'N/A')
            phone = contact_info.get('phone', 'N/A')
            print(f"   • Email: {email}")
            print(f"   • Telefone: {phone}")
        
        # Informações de endereço
        address = client.get('address')
        if address:
            print(f"\n📍 Informações de Endereço:")
            street = address.get('street', 'N/A')
            city = address.get('city', 'N/A')
            state = address.get('state', 'N/A')
            postal_code = address.get('postalCode', 'N/A')
            country = address.get('country', 'N/A')
            
            print(f"   • Rua: {street}")
            print(f"   • Cidade: {city}")
            print(f"   • Estado: {state}")
            print(f"   • CEP: {postal_code}")
            print(f"   • País: {country}")
        
        # Links disponíveis
        links = client.get('links', [])
        if links:
            print(f"\n🔗 Endpoints disponíveis ({len(links)} total):")
            for link in links:
                rel = link.get('rel', 'N/A')
                uri = link.get('uri', 'N/A')
                print(f"   • {rel}: {uri}")

        # Informações detalhadas do cliente
        client_url = f"{API_BASE_URL}/organizations/{organization_id}/clients/{client_id}"
        print(f"\n🔍 Informações detalhadas do cliente: {client_url}")

def test_field_farms_and_clients():
    """
    Testa farms e clients em múltiplos campos
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
    
    print("🧪 Testando Farms e Clients em múltiplos campos...")
    
    for field in test_fields:
        print(f"\n{'='*80}")
        print(f"🌾 TESTANDO CAMPO: {field['name']} (ID: {field['id']})")
        print(f"{'='*80}")
        
        # Teste 1: Farms
        print(f"\n🏡 TESTE 1: Farms do campo")
        farms_data = get_field_farms(
            organization_id=organization_id,
            field_id=field['id']
        )
        
        if farms_data:
            analyze_farms(farms_data, organization_id)
        else:
            print("❌ Nenhuma fazenda encontrada para este campo.")
        
        # Teste 2: Clients
        print(f"\n👥 TESTE 2: Clients do campo")
        clients_data = get_field_clients(
            organization_id=organization_id,
            field_id=field['id']
        )
        
        if clients_data:
            analyze_clients(clients_data, organization_id)
        else:
            print("❌ Nenhum cliente encontrado para este campo.")

def main():
    """
    Função principal
    """
    print("🚀 Iniciando busca de Farms e Clients...")
    
    # Testar farms e clients em múltiplos campos
    test_field_farms_and_clients()
    
    print(f"\n✅ Análise completa concluída!")

if __name__ == "__main__":
    main() 