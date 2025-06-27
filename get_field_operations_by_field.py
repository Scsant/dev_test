#!/usr/bin/env python3
"""
Script para buscar operações de campo específicas de um campo da John Deere
Usando o endpoint: /organizations/{orgId}/fields/{fieldId}/fieldOperations
"""

import os
import json
import requests
import time
from typing import Dict, Any, Optional
from datetime import datetime, timedelta

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

def get_field_operations_by_field(
    organization_id: str, 
    field_id: str,
    crop_season: Optional[int] = None,
    field_operation_type: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    embed: Optional[str] = None,
    work_plan_ids: Optional[list] = None
) -> Dict[str, Any]:
    """
    Busca operações de campo específicas de um campo
    
    Args:
        organization_id: ID da organização
        field_id: GUID do campo
        crop_season: Ano da safra (ex: 2024)
        field_operation_type: Tipo de operação ("APPLICATION", "HARVEST", "SEEDING", "TILLAGE")
        start_date: Data de início em ISO-8601 (ex: "2024-01-01T00:00:00Z")
        end_date: Data de fim em ISO-8601 (ex: "2024-12-31T23:59:59Z")
        embed: Para incluir measurementTypes
        work_plan_ids: Lista de IDs de planos de trabalho
    """
    tokens = get_valid_tokens()
    access_token = tokens.get('access_token')
    
    print(f"🔍 Buscando operações de campo para organização {organization_id}, campo {field_id}...")
    
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

def analyze_field_operations_by_field(field_ops_data: Dict[str, Any]) -> None:
    """
    Analisa e exibe informações das operações de campo de forma organizada
    """
    print("\n" + "="*80)
    print("🌾 ANÁLISE DAS OPERAÇÕES DE CAMPO ESPECÍFICAS")
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
    seasons_count = {}
    
    for op in operations:
        op_type = op.get('fieldOperationType', 'Desconhecido')
        crop_season = op.get('cropSeason', 'Desconhecida')
        
        types_count[op_type] = types_count.get(op_type, 0) + 1
        seasons_count[crop_season] = seasons_count.get(crop_season, 0) + 1
    
    print(f"\n📈 Operações por tipo:")
    for op_type, count in types_count.items():
        print(f"   • {op_type}: {count}")
    
    print(f"\n🌾 Operações por safra:")
    for season, count in seasons_count.items():
        print(f"   • {season}: {count}")

def main():
    """
    Função principal
    """
    # Configurações - ajuste conforme necessário
    organization_id = "368927"  # BSPF - 2025
    field_id = "d61b83f4-3a12-431e-8010-596f2466dc27"  # Exemplo de GUID de campo
    
    # Parâmetros opcionais - descomente e ajuste conforme necessário
    # crop_season = 2024
    # field_operation_type = "APPLICATION"  # APPLICATION, HARVEST, SEEDING, TILLAGE
    # start_date = "2024-01-01T00:00:00Z"
    # end_date = "2024-12-31T23:59:59Z"
    # embed = "measurementTypes"
    
    print("🚀 Iniciando busca de operações de campo específicas...")
    print(f"📋 Configuração:")
    print(f"   • Organização: {organization_id}")
    print(f"   • Campo: {field_id}")
    
    # Buscar operações de campo
    field_ops_data = get_field_operations_by_field(
        organization_id=organization_id,
        field_id=field_id
        # crop_season=crop_season,
        # field_operation_type=field_operation_type,
        # start_date=start_date,
        # end_date=end_date,
        # embed=embed
    )
    
    if field_ops_data:
        # Exibir dados brutos (opcional)
        print(f"\n📄 Dados brutos da resposta:")
        print(json.dumps(field_ops_data, indent=2))
        
        # Análise detalhada
        analyze_field_operations_by_field(field_ops_data)
        
        # Resumo
        print_field_operations_summary(field_ops_data)
        
        print(f"\n✅ Análise concluída!")
    else:
        print("❌ Falha ao obter operações de campo.")

if __name__ == "__main__":
    main() 