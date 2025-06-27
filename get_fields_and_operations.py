#!/usr/bin/env python3
"""
Script completo para buscar campos da organização e suas operações
Fluxo: Organização → Campos → Operações de Campo
"""

import os
import json
import requests
import time
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta

API_BASE_URL = "https://sandboxapi.deere.com/platform"
TOKEN_URL = "https://signin.johndeere.com/oauth2/aus78tnlaysMraFhC1t7/v1/token"
CLIENT_ID = "0oap8bfnk7ViKFk7M5d7"
CLIENT_SECRET = "usklX-2OR8SHRY9pziQ-uMS3qzxkwYR_ZpFatiuQtFPaWVi6NrmhZW9RQvFjVYlL"
REDIRECT_URI = "http://localhost:9090/callback"
SCOPES = "ag1 ag2 org1 eq1 offline_access"  # Incluindo ag2 para operações de campo

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

def get_organization_fields(
    organization_id: str,
    client_name: Optional[str] = None,
    farm_name: Optional[str] = None,
    field_name: Optional[str] = None,
    embed: Optional[str] = None,
    record_filter: Optional[str] = None,
    uom_system: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    """
    Busca todos os campos de uma organização
    
    Args:
        organization_id: ID da organização
        client_name: Nome do cliente (filtro)
        farm_name: Nome da fazenda (filtro)
        field_name: Nome do campo (filtro)
        embed: Lista de objetos para incluir
        record_filter: Filtro por estado (AVAILABLE, ARCHIVED, ALL)
        uom_system: Sistema de unidades (METRIC, ENGLISH)
    """
    tokens = get_valid_tokens()
    access_token = tokens.get('access_token')
    
    print(f"🔍 Buscando campos da organização {organization_id}...")
    
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Accept': 'application/vnd.deere.axiom.v3+json'
    }
    
    if uom_system:
        headers['Accept-UOM-System'] = uom_system
    
    # URL do endpoint
    fields_url = f"{API_BASE_URL}/organizations/{organization_id}/fields"
    
    # Parâmetros de query
    params = {}
    if client_name:
        params['clientName'] = client_name
    if farm_name:
        params['farmName'] = farm_name
    if field_name:
        params['fieldName'] = field_name
    if embed:
        params['embed'] = embed
    if record_filter:
        params['recordFilter'] = record_filter
    
    try:
        print(f"📡 Fazendo requisição para: {fields_url}")
        if params:
            print(f"📋 Parâmetros: {params}")
        
        response = requests.get(fields_url, headers=headers, params=params)
        
        print(f"📊 Status da resposta: {response.status_code}")
        print(f"📋 Headers da resposta: {dict(response.headers)}")
        
        response.raise_for_status()
        fields_data = response.json()
        
        print("✅ Campos obtidos com sucesso!")
        return fields_data
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Erro ao buscar campos: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"📊 Status de erro: {e.response.status_code}")
            print(f"📄 Resposta de erro: {e.response.text}")
        return None

def get_field_operations_by_field(
    organization_id: str, 
    field_id: str,
    crop_season: Optional[int] = None,
    field_operation_type: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    embed: Optional[str] = None,
    work_plan_ids: Optional[list] = None
) -> Optional[Dict[str, Any]]:
    """
    Busca operações de campo específicas de um campo
    """
    tokens = get_valid_tokens()
    access_token = tokens.get('access_token')
    
    print(f"🔍 Buscando operações de campo para campo {field_id}...")
    
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Accept': 'application/vnd.deere.axiom.v3+json'
    }
    
    # URL base do endpoint
    field_ops_url = f"{API_BASE_URL}/organizations/{organization_id}/fields/{field_id}/fieldOperations"
    
    # Parâmetros de query
    params = {}
    if crop_season:
        params['cropSeason'] = crop_season
    if field_operation_type:
        params['fieldOperationType'] = field_operation_type
    if start_date:
        params['startDate'] = start_date
    if end_date:
        params['endDate'] = end_date
    if embed:
        params['embed'] = embed
    if work_plan_ids:
        params['workPlanIds'] = work_plan_ids
    
    try:
        print(f"📡 Fazendo requisição para: {field_ops_url}")
        if params:
            print(f"📋 Parâmetros: {params}")
        
        response = requests.get(field_ops_url, headers=headers, params=params)
        
        print(f"📊 Status da resposta: {response.status_code}")
        
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

def analyze_fields(fields_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Analisa e exibe informações dos campos de forma organizada
    Retorna lista de campos para seleção
    """
    print("\n" + "="*80)
    print("🌾 ANÁLISE DOS CAMPOS DA ORGANIZAÇÃO")
    print("="*80)
    
    if not fields_data:
        print("❌ Nenhum dado de campos para analisar.")
        return []
    
    # Informações gerais
    total_fields = fields_data.get('total', 0)
    print(f"\n📈 Total de campos: {total_fields}")
    
    # Links da resposta principal
    main_links = fields_data.get('links', [])
    if main_links:
        print(f"\n🔗 Links principais:")
        for link in main_links:
            print(f"   • {link.get('rel', 'N/A')}: {link.get('uri', 'N/A')}")
    
    # Processar cada campo
    fields = fields_data.get('values', [])
    
    if not fields:
        print("\n📭 Nenhum campo encontrado.")
        return []
    
    print(f"\n📋 Campos disponíveis:")
    available_fields = []
    
    for i, field in enumerate(fields, 1):
        field_id = field.get('id', 'N/A')
        field_name = field.get('name', 'N/A')
        archived = field.get('archived', False)
        
        print(f"\n{'='*50}")
        print(f"🌾 CAMPO {i}/{len(fields)}")
        print(f"{'='*50}")
        
        print(f"📋 Informações Básicas:")
        print(f"   • ID: {field_id}")
        print(f"   • Nome: {field_name}")
        print(f"   • Arquivado: {'✅ Sim' if archived else '❌ Não'}")
        
        # Informações de fazendas
        farms = field.get('farms', [])
        if farms:
            print(f"\n🏡 Fazendas:")
            for farm in farms:
                farm_name = farm.get('name', 'N/A')
                farm_id = farm.get('id', 'N/A')
                print(f"   • {farm_name} (ID: {farm_id})")
        
        # Informações de clientes
        clients = field.get('clients', [])
        if clients:
            print(f"\n👥 Clientes:")
            for client in clients:
                client_name = client.get('name', 'N/A')
                client_id = client.get('id', 'N/A')
                print(f"   • {client_name} (ID: {client_id})")
        
        # Links disponíveis
        links = field.get('links', [])
        if links:
            print(f"\n🔗 Endpoints disponíveis ({len(links)} total):")
            for link in links:
                rel = link.get('rel', 'N/A')
                uri = link.get('uri', 'N/A')
                print(f"   • {rel}: {uri}")
        
        # Adicionar à lista de campos disponíveis (apenas não arquivados)
        if not archived:
            available_fields.append({
                'index': i,
                'id': field_id,
                'name': field_name,
                'farms': farms,
                'clients': clients
            })
    
    return available_fields

def select_field(fields: List[Dict[str, Any]]) -> Optional[str]:
    """
    Permite ao usuário selecionar um campo
    """
    if not fields:
        print("❌ Nenhum campo disponível para seleção.")
        return None
    
    print(f"\n{'='*80}")
    print("🎯 SELEÇÃO DE CAMPO")
    print(f"{'='*80}")
    
    print(f"\n📋 Campos disponíveis para consulta de operações:")
    for field in fields:
        print(f"   {field['index']}. {field['name']} (ID: {field['id']})")
    
    while True:
        try:
            choice = input(f"\n🔢 Escolha um campo (1-{len(fields)}) ou 'q' para sair: ").strip()
            
            if choice.lower() == 'q':
                return None
            
            choice_num = int(choice)
            if 1 <= choice_num <= len(fields):
                selected_field = fields[choice_num - 1]
                print(f"\n✅ Campo selecionado: {selected_field['name']} (ID: {selected_field['id']})")
                return selected_field['id']
            else:
                print(f"❌ Opção inválida. Escolha um número entre 1 e {len(fields)}.")
        except ValueError:
            print("❌ Entrada inválida. Digite um número ou 'q' para sair.")

def analyze_field_operations(field_ops_data: Dict[str, Any]) -> None:
    """
    Analisa e exibe informações das operações de campo
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
        op_type = operation.get('fieldOperationType', 'N/A')
        crop_season = operation.get('cropSeason', 'N/A')
        adapt_machine_type = operation.get('adaptMachineType', 'N/A')
        
        print(f"📋 Informações Básicas:")
        print(f"   • ID: {op_id}")
        print(f"   • Tipo: {op_type}")
        print(f"   • Safra: {crop_season}")
        print(f"   • Tipo de Máquina: {adapt_machine_type}")
        
        # Informações de data/hora
        start_date = operation.get('startDate', 'N/A')
        end_date = operation.get('endDate', 'N/A')
        modified_time = operation.get('modifiedTime', 'N/A')
        
        print(f"\n📅 Informações de Data/Hora:")
        print(f"   • Data de início: {start_date}")
        print(f"   • Data de fim: {end_date}")
        print(f"   • Última modificação: {modified_time}")
        
        # Informações de produtos (para aplicações)
        products = operation.get('products')
        if products:
            print(f"\n🧪 Informações de Produtos:")
            product_name = products.get('name', 'N/A')
            tank_mix = products.get('tankMix', False)
            print(f"   • Nome: {product_name}")
            print(f"   • Tank Mix: {'✅ Sim' if tank_mix else '❌ Não'}")
            
            # Taxa de aplicação
            rate = products.get('rate')
            if rate:
                value = rate.get('value', 'N/A')
                unit = rate.get('unitId', 'N/A')
                print(f"   • Taxa: {value} {unit}")
            
            # Componentes (para tank mixes)
            components = products.get('components', [])
            if components:
                print(f"   • Componentes:")
                for comp in components:
                    comp_name = comp.get('name', 'N/A')
                    comp_rate = comp.get('rate', {})
                    comp_value = comp_rate.get('value', 'N/A')
                    comp_unit = comp_rate.get('unitId', 'N/A')
                    print(f"     - {comp_name}: {comp_value} {comp_unit}")
        
        # Informações de máquinas
        machines = operation.get('fieldOperationMachines', [])
        if machines:
            print(f"\n🚜 Máquinas Utilizadas:")
            for machine in machines:
                machine_id = machine.get('machineId', 'N/A')
                vin = machine.get('vin', 'N/A')
                erid = machine.get('erid', 'N/A')
                print(f"   • ID: {machine_id}, VIN: {vin}, ERID: {erid}")
                
                # Operadores
                operators = machine.get('operators', [])
                if operators:
                    print(f"     Operadores:")
                    for op in operators:
                        op_name = op.get('name', 'N/A')
                        op_license = op.get('license', 'N/A')
                        print(f"       - {op_name} (Licença: {op_license})")

def main():
    """
    Função principal
    """
    # Configuração
    organization_id = "5881930"  # BSPF - 2025
    
    print("🚀 Iniciando busca de campos e operações...")
    print(f"📋 Configuração:")
    print(f"   • Organização: {organization_id}")
    
    # 1. Buscar campos da organização
    print(f"\n{'='*80}")
    print("📋 ETAPA 1: BUSCANDO CAMPOS DA ORGANIZAÇÃO")
    print(f"{'='*80}")
    
    fields_data = get_organization_fields(
        organization_id=organization_id
    )
    
    if not fields_data:
        print("❌ Falha ao obter campos da organização.")
        return
    
    # 2. Analisar campos e permitir seleção
    available_fields = analyze_fields(fields_data)
    
    if not available_fields:
        print("❌ Nenhum campo disponível para consulta.")
        return
    
    # 3. Selecionar campo
    selected_field_id = select_field(available_fields)
    
    if not selected_field_id:
        print("❌ Nenhum campo selecionado.")
        return
    
    # 4. Buscar operações do campo selecionado
    print(f"\n{'='*80}")
    print("📋 ETAPA 2: BUSCANDO OPERAÇÕES DO CAMPO SELECIONADO")
    print(f"{'='*80}")
    
    field_ops_data = get_field_operations_by_field(
        organization_id=organization_id,
        field_id=selected_field_id
    )
    
    if field_ops_data:
        # 5. Analisar operações
        analyze_field_operations(field_ops_data)
        
        # 6. Exibir dados brutos (opcional)
        print(f"\n📄 Dados brutos das operações:")
        print(json.dumps(field_ops_data, indent=2))
        
        print(f"\n✅ Análise completa concluída!")
    else:
        print("❌ Falha ao obter operações de campo.")

if __name__ == "__main__":
    main() 