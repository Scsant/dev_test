import requests
import urllib.parse
import json
import http.server
import socketserver
import webbrowser
import threading
import time
import os
from analyze_organizations import analyze_organizations, get_organization_summary, print_summary

# --- Seus dados da Aplicação John Deere ---
# Substitua com seus valores reais do Developer.Deere.com
CLIENT_ID = "0oap8bfnk7ViKFk7M5d7"
CLIENT_SECRET = "usklX-2OR8SHRY9pziQ-uMS3qzxkwYR_ZpFatiuQtFPaWVi6NrmhZW9RQvFjVYlL"
REDIRECT_URI = "http://localhost:9090/callback" # Deve ser uma das URIs configuradas na sua aplicação John Deere
SCOPES = "ag1 ag2 ag3 org1 eq1 files offline_access" # Escopos atualizados para incluir files e ag3

# --- URLs da API John Deere (descobertas do .well-known) ---
# Você pode chamar o .well-known endpoint para obter estes ou usá-los diretamente se eles forem fixos.
# Para este exemplo, vamos usar os que você forneceu.
AUTHORIZATION_BASE_URL = "https://signin.johndeere.com/oauth2/aus78tnlaysMraFhC1t7/v1/authorize"
TOKEN_URL = "https://signin.johndeere.com/oauth2/aus78tnlaysMraFhC1t7/v1/token"
WELL_KNOWN_URL = "https://signin.johndeere.com/oauth2/aus78tnlaysMraFhC1t7/.well-known/oauth-authorization-server"
API_BASE_URL = "https://sandboxapi.deere.com/platform" # ou a URL da API de produção se aplicável

# Variáveis para armazenar o código de autorização e tokens
authorization_code = None
access_token = None
refresh_token = None
expires_in = None # Tempo de expiração do access token em segundos
token_acquired_time = None # Timestamp quando o token foi adquirido

# --- Função para iniciar um servidor web local para o callback ---
# Este servidor vai capturar o código de autorização após o login do usuário
class OAuth2CallbackHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        global authorization_code
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        
        query_params = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
        
        if 'code' in query_params:
            authorization_code = query_params['code'][0]
            self.wfile.write("<h1>Autenticação John Deere Concluída!</h1>".encode('utf-8'))
            self.wfile.write("<p>Você pode fechar esta aba e voltar para o terminal.</p>".encode('utf-8'))
            print(f"Código de autorização recebido: {authorization_code}")
            # Após receber o código, desliga o servidor para evitar que ele fique rodando
            threading.Thread(target=self.server.shutdown).start()
        elif 'error' in query_params:
            error = query_params['error'][0]
            error_description = query_params.get('error_description', [''])[0]
            self.wfile.write(f"<h1>Erro na Autenticação!</h1>".encode('utf-8'))
            self.wfile.write(f"<p>Erro: {error}</p>".encode('utf-8'))
            self.wfile.write(f"<p>Descrição: {error_description}</p>".encode('utf-8'))
            print(f"Erro na autenticação: {error} - {error_description}")
            threading.Thread(target=self.server.shutdown).start()
        else:
            self.wfile.write("<h1>Aguardando código de autorização...</h1>".encode('utf-8'))
            print("Aguardando código de autorização...")

def start_local_server():
    """Inicia um servidor HTTP local para capturar o callback OAuth."""
    port = urllib.parse.urlparse(REDIRECT_URI).port
    if not port:
        raise ValueError("REDIRECT_URI must include a port, e.g., http://localhost:9090/callback")
    
    with socketserver.TCPServer(("", port), OAuth2CallbackHandler) as httpd:
        print(f"Servidor local iniciado na porta {port}. Aguardando callback...")
        httpd.serve_forever()

# --- Funções para o fluxo OAuth ---

def discover_oauth_endpoints():
    """Faz a requisição ao .well-known URL para obter os endpoints."""
    print("Descobrindo endpoints OAuth da John Deere...")
    try:
        response = requests.get(WELL_KNOWN_URL)
        response.raise_for_status() # Lança exceção para status de erro (4xx ou 5xx)
        well_known_config = response.json()
        print("Endpoints descobertos com sucesso:")
        print(json.dumps(well_known_config, indent=2))
        
        # Você pode atualizar as URLs se necessário, mas para o caso da JD elas são fixas
        # AUTHORIZATION_BASE_URL = well_known_config['authorization_endpoint']
        # TOKEN_URL = well_known_config['token_endpoint']
        return well_known_config
    except requests.exceptions.RequestException as e:
        print(f"Erro ao descobrir endpoints OAuth: {e}")
        return None

def get_authorization_code():
    """Redireciona o usuário para a URL de autorização e aguarda o código."""
    global authorization_code

    # Gere um 'state' para proteção CSRF
    state = "some_random_state_string_for_security" # Em um app real, use algo mais robusto, como UUID.uuid4().hex

    auth_url = (
        f"{AUTHORIZATION_BASE_URL}?"
        f"response_type=code&"
        f"scope={urllib.parse.quote(SCOPES)}&" # Assegura que os escopos estejam corretamente codificados para URL
        f"client_id={CLIENT_ID}&"
        f"state={state}&"
        f"redirect_uri={urllib.parse.quote(REDIRECT_URI, safe='')}" # Assegura que o URI de redirecionamento esteja codificado
    )

    print(f"\nPor favor, abra esta URL no seu navegador para autorizar a aplicação:")
    print(auth_url)
    
    # Abrir no navegador automaticamente (pode não funcionar em todos os ambientes)
    webbrowser.open(auth_url)

    # Inicia o servidor local em uma thread separada para não bloquear o programa principal
    server_thread = threading.Thread(target=start_local_server)
    server_thread.daemon = True # Permite que a thread seja encerrada quando o programa principal terminar
    server_thread.start()

    # Espera até que o código de autorização seja recebido
    while authorization_code is None:
        time.sleep(1) # Espera 1 segundo antes de verificar novamente

    return authorization_code

def get_tokens(auth_code):
    """Troca o código de autorização por um access_token e refresh_token."""
    global access_token, refresh_token, expires_in, token_acquired_time
    
    print("\nSolicitando token de acesso...")
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
        'Accept': 'application/json'
    }
    data = {
        'grant_type': 'authorization_code',
        'code': auth_code,
        'redirect_uri': REDIRECT_URI,
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET
    }

    try:
        response = requests.post(TOKEN_URL, headers=headers, data=data, verify=False) # 'verify=True' para garantir que a conexão é segura
        response.raise_for_status()
        token_data = response.json()

        access_token = token_data.get('access_token')
        refresh_token = token_data.get('refresh_token')
        expires_in = token_data.get('expires_in')
        token_acquired_time = time.time() # Registra o tempo de aquisição
        
        print("Tokens recebidos com sucesso!")
        print(f"Access Token (parcial): {access_token[:10]}...")
        if refresh_token:
            print(f"Refresh Token (parcial): {refresh_token[:10]}...")
        print(f"Expira em: {expires_in} segundos")
        return token_data
    except requests.exceptions.RequestException as e:
        print(f"Erro ao obter tokens: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"Resposta de erro: {e.response.text}")
        return None

def refresh_access_token():
    """Usa o refresh_token para obter um novo access_token."""
    global access_token, refresh_token, expires_in, token_acquired_time
    
    if not refresh_token:
        print("Erro: Refresh Token não disponível. Reautentique-se.")
        return False

    print("\nAtualizando token de acesso com refresh token...")
    headers = {
        'Accept': 'application/json',
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    data = {
        'grant_type': 'refresh_token',
        'refresh_token': refresh_token,
        'redirect_uri': REDIRECT_URI,
        'scope': SCOPES, # É uma boa prática enviar os escopos novamente ao renovar
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET
    }

    try:
        response = requests.post(TOKEN_URL, headers=headers, data=data, verify=False) # 'verify=True' para garantir que a conexão é segura
        response.raise_for_status()
        token_data = response.json()

        access_token = token_data.get('access_token')
        # O refresh token pode ser rotativo, então é bom atualizar ele também
        refresh_token = token_data.get('refresh_token', refresh_token) 
        expires_in = token_data.get('expires_in')
        token_acquired_time = time.time()
        
        print("Token de acesso atualizado com sucesso!")
        print(f"Novo Access Token (parcial): {access_token[:10]}...")
        print(f"Expira em: {expires_in} segundos")
        return True
    except requests.exceptions.RequestException as e:
        print(f"Erro ao refrescar token: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"Resposta de erro: {e.response.text}")
        return False

def is_token_expired_or_expiring(grace_period=60):
    """Verifica se o token está expirado ou prestes a expirar."""
    if not access_token or not expires_in or not token_acquired_time:
        return True # Token não existe ou dados incompletos

    # Calcula o tempo restante até a expiração
    time_elapsed = time.time() - token_acquired_time
    time_remaining = expires_in - time_elapsed
    
    return time_remaining <= grace_period # Expira em menos de 'grace_period' segundos

def ensure_token_valid():
    """Garante que temos um token de acesso válido, renovando se necessário."""
    if is_token_expired_or_expiring():
        print("Token de acesso expirado ou prestes a expirar. Tentando renovar...")
        if not refresh_access_token():
            print("Falha ao renovar o token. O usuário precisará se reautenticar.")
            return False
    return True

def get_organizations():
    """Tenta buscar as organizações e verifica a necessidade de conexão."""
    global access_token
    
    if not ensure_token_valid():
        return None, "Token inválido ou não foi possível renovar."

    print("\nBuscando organizações e verificando conexões...")
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Accept': 'application/vnd.deere.axiom.v3+json' # Exemplo de header para a API, verifique a documentação para o endpoint correto
    }
    
    try:
        # Este é um endpoint de exemplo. Confirme o endpoint real no próximo prompt.
        orgs_url = f"{API_BASE_URL}/organizations" 
        print(f"Fazendo requisição para: {orgs_url}")
        response = requests.get(orgs_url, headers=headers, verify=False) # 'verify=True' para garantir que a conexão é segura   
        
        print(f"Status da resposta: {response.status_code}")
        print(f"Headers da resposta: {dict(response.headers)}")
        
        response.raise_for_status()
        organizations = response.json()
        
        print("Organizações obtidas com sucesso!")
        print(f"Tipo de resposta: {type(organizations)}")
        print(f"Conteúdo da resposta: {json.dumps(organizations, indent=2)}")
        
        return organizations, None
    except requests.exceptions.RequestException as e:
        print(f"Erro ao buscar organizações: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"Status de erro: {e.response.status_code}")
            print(f"Resposta de erro: {e.response.text}")
        return None, f"Erro ao buscar organizações: {e}"

def handle_organization_connection(organizations_data):
    """Verifica se há conexões pendentes e orienta o usuário."""
    if not organizations_data:
        print("Nenhum dado de organização para processar.")
        return False

    # Verifica se organizations_data é uma string (pode ser uma mensagem de erro)
    if isinstance(organizations_data, str):
        print(f"Resposta da API: {organizations_data}")
        return False

    # Verifica se organizations_data é um dicionário com uma lista de organizações
    if isinstance(organizations_data, dict):
        # A API pode retornar os dados em diferentes formatos
        # Tenta encontrar a lista de organizações
        orgs_list = organizations_data.get('values', [])
        if not orgs_list:
            orgs_list = organizations_data.get('organizations', [])
        if not orgs_list:
            orgs_list = organizations_data.get('data', [])
        if not orgs_list:
            # Se não encontrar uma lista específica, assume que o próprio dicionário é uma organização
            orgs_list = [organizations_data]
    elif isinstance(organizations_data, list):
        orgs_list = organizations_data
    else:
        print(f"Formato de dados inesperado: {type(organizations_data)}")
        print(f"Conteúdo: {organizations_data}")
        return False

    print(f"Processando {len(orgs_list)} organização(s)...")

    for org in orgs_list:
        # Verifica se org é um dicionário válido
        if not isinstance(org, dict):
            print(f"Organização inválida (não é um dicionário): {org}")
            continue

        # Procura por links de conexão
        links = org.get('links', [])
        if not links:
            print(f"Organização '{org.get('name', 'Sem nome')}' não possui links de conexão.")
            continue

        for link in links:
            if isinstance(link, dict) and link.get('rel') == 'connections':
                connections_uri = link.get('uri')
                if connections_uri:
                    org_name = org.get('name', 'Sem nome')
                    org_id = org.get('id', 'Sem ID')
                    print(f"\nATENÇÃO: A organização '{org_name}' ({org_id}) requer conexão.")
                    print("Por favor, abra a seguinte URL no navegador para conceder acesso:")
                    
                    # Codifique o REDIRECT_URI para ser passado como parâmetro na URL de conexão
                    encoded_redirect_uri = urllib.parse.quote(REDIRECT_URI, safe='')
                    
                    # Exemplo: https://connections.deere.com/connections/{clientId}/select-organizations?redirect_uri={redirectUri}
                    connection_url_with_redirect = f"{connections_uri}?redirect_uri={encoded_redirect_uri}"
                    
                    print(connection_url_with_redirect)
                    webbrowser.open(connection_url_with_redirect)
                    print("\nApós selecionar as organizações, você será redirecionado de volta para sua aplicação (este script).")
                    print("Você precisará executar o script novamente para verificar as conexões.")
                    return True # Indica que uma ação do usuário é necessária

    print("Nenhuma conexão pendente encontrada.")
    return False # Nenhuma conexão pendente encontrada

def save_tokens():
    """Salva os tokens em um arquivo tokens.json."""
    global access_token, refresh_token, expires_in, token_acquired_time
    data = {
        'access_token': access_token,
        'refresh_token': refresh_token,
        'expires_in': expires_in,
        'token_acquired_time': token_acquired_time
    }
    with open('tokens.json', 'w', encoding='utf-8') as f:
        json.dump(data, f)
    print("Tokens salvos em tokens.json.")

def load_tokens():
    """Carrega os tokens do arquivo tokens.json, se existir."""
    global access_token, refresh_token, expires_in, token_acquired_time
    if os.path.exists('tokens.json'):
        with open('tokens.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
            access_token = data.get('access_token')
            refresh_token = data.get('refresh_token')
            expires_in = data.get('expires_in')
            token_acquired_time = data.get('token_acquired_time')
        print("Tokens carregados de tokens.json.")
    else:
        print("tokens.json não encontrado. Será necessário autenticar.")

# --- Fluxo Principal de Autenticação ---
if __name__ == "__main__":
    # Carrega tokens se existirem
    load_tokens()
    # 1. Descobrir Endpoints (Opcional, mas boa prática)
    # well_known_config = discover_oauth_endpoints()
    # if not well_known_config:
    #     exit("Não foi possível obter a configuração OAuth. Verifique a URL ou sua conexão.")

    # 2. Obter Código de Autorização
    if not access_token or not refresh_token:
        print("Iniciando processo de autenticação com John Deere...")
        auth_code = get_authorization_code()
        
        if auth_code:
            print(f"Código de Autorização obtido: {auth_code}")
            # 3. Trocar Código por Access Token e Refresh Token
            token_response = get_tokens(auth_code)
            if token_response:
                save_tokens()
                print("Autenticação inicial concluída!")
            else:
                print("Falha ao obter tokens. Processo de autenticação abortado.")
                exit(1)
        else:
            print("Falha ao obter o código de autorização. Processo de autenticação abortado.")
            exit(1)
    else:
        print("Tokens já carregados. Pulando autenticação inicial.")

    # 4. Verificar e Habilitar Acesso à Organização
    organizations, error = get_organizations()
    if organizations:
        if handle_organization_connection(organizations):
            print("\n--- Por favor, complete a conexão de organização no navegador. ---")
            print("--- Após isso, execute o script novamente para verificar e prosseguir. ---")
        else:
            print("\nAcesso às organizações já habilitado ou nenhuma conexão pendente.")
            
            # 5. Analisar e exibir informações das organizações
            print("\n" + "="*80)
            print("📊 ANÁLISE DETALHADA DAS ORGANIZAÇÕES")
            print("="*80)
            
            # Análise completa
            analyze_organizations(organizations)
            
            # Resumo executivo
            summary = get_organization_summary(organizations)
            print_summary(summary)
            
            print("\n--- Agora você pode fazer requisições à API com o token de acesso. ---")
            print("\n💡 Dicas de uso:")
            print("   • Use os endpoints listados acima para acessar dados específicos")
            print("   • O token de acesso está disponível na variável 'access_token'")
            print("   • Para renovar o token automaticamente, use 'ensure_token_valid()'")
            print("   • Exemplo: response = requests.get(endpoint_url, headers={'Authorization': f'Bearer {access_token}'})")
            
            # Exemplo de como você usaria o token para uma requisição
            # Seu próximo passo seria definir uma função para usar 'access_token'
            # e 'API_BASE_URL' para acessar os endpoints que você mencionará.
            # Ex: response = requests.get(f"{API_BASE_URL}/some_endpoint", headers={'Authorization': f'Bearer {access_token}'})
    else:
        print(f"Erro ao verificar organizações: {error}")

    print("\nFim do script principal de autenticação.")