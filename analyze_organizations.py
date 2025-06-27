#!/usr/bin/env python3
"""
Script para analisar e exibir informações das organizações da John Deere
"""

import json
from typing import Dict, List, Any

def analyze_organizations(organizations_data: Dict[str, Any]) -> None:
    """
    Analisa e exibe informações das organizações de forma organizada
    """
    print("=" * 80)
    print("📊 ANÁLISE DAS ORGANIZAÇÕES JOHN DEERE")
    print("=" * 80)
    
    # Informações gerais
    total_orgs = organizations_data.get('total', 0)
    print(f"\n📈 Total de organizações: {total_orgs}")
    
    # Links da resposta principal
    main_links = organizations_data.get('links', [])
    if main_links:
        print(f"\n🔗 Links principais:")
        for link in main_links:
            print(f"   • {link.get('rel', 'N/A')}: {link.get('uri', 'N/A')}")
    
    # Processar cada organização
    organizations = organizations_data.get('values', [])
    
    for i, org in enumerate(organizations, 1):
        print(f"\n{'='*60}")
        print(f"🏢 ORGANIZAÇÃO {i}/{len(organizations)}")
        print(f"{'='*60}")
        
        # Informações básicas
        org_id = org.get('id', 'N/A')
        org_name = org.get('name', 'N/A')
        org_type = org.get('type', 'N/A')
        is_member = org.get('member', False)
        is_internal = org.get('internal', False)
        hierarchy_enabled = org.get('hierarchyEnabled', False)
        
        print(f"📋 Informações Básicas:")
        print(f"   • ID: {org_id}")
        print(f"   • Nome: {org_name}")
        print(f"   • Tipo: {org_type}")
        print(f"   • Membro: {'✅ Sim' if is_member else '❌ Não'}")
        print(f"   • Interna: {'✅ Sim' if is_internal else '❌ Não'}")
        print(f"   • Hierarquia habilitada: {'✅ Sim' if hierarchy_enabled else '❌ Não'}")
        
        # Categorizar links por funcionalidade
        links = org.get('links', [])
        if links:
            print(f"\n🔗 Endpoints disponíveis ({len(links)} total):")
            
            # Categorias de endpoints
            categories = {
                '🏭 Máquinas e Equipamentos': ['machines', 'implements', 'wdtCapableMachines', 'addMachine'],
                '🌾 Agricultura': ['fields', 'farms', 'boundaries', 'addField', 'fieldOperation', 'fieldGuidSearch'],
                '🧪 Produtos': ['chemicals', 'fertilizers', 'varieties', 'tankMixes', 'addChemical', 'addFertilizer', 'addVariety', 'addTankMix'],
                '👥 Pessoas': ['staff', 'addStaff', 'operators'],
                '📁 Arquivos': ['files', 'transferableFiles', 'uploadFile', 'sendFileToMachine'],
                '⚙️ Manutenção': ['organizationMaintenancePlans', 'organizationMaintenancePlansList'],
                '🔔 Notificações': ['notifications'],
                '⚡ Ativações': ['activateProduct', 'contributionActivation'],
                '📋 Tarefas': ['tasks'],
                '🏷️ Preferências': ['preferences', 'machineStylePreferences'],
                '🎯 Outros': ['assets', 'clients', 'flags', 'flagCategory', 'displays', 'entitySyncEnrollments', 'manage_connection']
            }
            
            for category, rel_types in categories.items():
                category_links = [link for link in links if link.get('rel') in rel_types]
                if category_links:
                    print(f"\n   {category}:")
                    for link in category_links:
                        rel = link.get('rel', 'N/A')
                        uri = link.get('uri', 'N/A')
                        print(f"     • {rel}: {uri}")

def get_organization_summary(organizations_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Retorna um resumo das organizações
    """
    organizations = organizations_data.get('values', [])
    
    summary = {
        'total_organizations': len(organizations),
        'organizations': []
    }
    
    for org in organizations:
        org_summary = {
            'id': org.get('id'),
            'name': org.get('name'),
            'type': org.get('type'),
            'member': org.get('member'),
            'total_endpoints': len(org.get('links', [])),
            'key_endpoints': []
        }
        
        # Adicionar endpoints principais
        links = org.get('links', [])
        key_endpoints = ['machines', 'fields', 'chemicals', 'fertilizers', 'varieties', 'staff']
        for link in links:
            if link.get('rel') in key_endpoints:
                org_summary['key_endpoints'].append(link.get('rel'))
        
        summary['organizations'].append(org_summary)
    
    return summary

def print_summary(summary: Dict[str, Any]) -> None:
    """
    Imprime um resumo das organizações
    """
    print(f"\n{'='*80}")
    print("📋 RESUMO EXECUTIVO")
    print(f"{'='*80}")
    
    print(f"\n📊 Total de organizações: {summary['total_organizations']}")
    
    for i, org in enumerate(summary['organizations'], 1):
        print(f"\n🏢 Organização {i}: {org['name']} (ID: {org['id']})")
        print(f"   • Tipo: {org['type']}")
        print(f"   • Membro: {'✅ Sim' if org['member'] else '❌ Não'}")
        print(f"   • Total de endpoints: {org['total_endpoints']}")
        print(f"   • Principais funcionalidades: {', '.join(org['key_endpoints'])}")

# Exemplo de uso (você pode importar essas funções no seu script principal)
if __name__ == "__main__":
    # Exemplo de dados (substitua pelos dados reais da sua API)
    sample_data = {
        "links": [{"@type": "Link", "rel": "self", "uri": "https://sandboxapi.deere.com/platform/organizations"}],
        "total": 3,
        "values": [
            {
                "@type": "Organization",
                "name": "Exemplo Org",
                "type": "customer",
                "member": True,
                "id": "123",
                "links": []
            }
        ]
    }
    
    print("Este script deve ser importado e usado com dados reais da API.")
    print("Exemplo de uso:")
    print("from analyze_organizations import analyze_organizations, get_organization_summary, print_summary")
    print("analyze_organizations(organizations_data)") 