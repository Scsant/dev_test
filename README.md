# John Deere API Integration

Este projeto implementa a integração com a API da John Deere usando OAuth 2.0 para autenticação.

## Pré-requisitos

- Python 3.7 ou superior
- Conta de desenvolvedor na John Deere (Developer.Deere.com)
- Aplicação configurada no portal de desenvolvedores da John Deere

## Instalação

1. Clone o repositório:
```bash
git clone <url-do-repositorio>
cd jd
```

2. Crie um ambiente virtual:
```bash
python -m venv venv
```

3. Ative o ambiente virtual:

**Windows (PowerShell):**
```powershell
.\venv\Scripts\Activate.ps1
```

**Windows (Command Prompt):**
```cmd
.\venv\Scripts\activate.bat
```

**Linux/macOS:**
```bash
source venv/bin/activate
```

4. Instale as dependências:
```bash
pip install -r requirements.txt
```

## Configuração

1. Acesse [Developer.Deere.com](https://developer.deere.com) e crie uma aplicação
2. Configure as seguintes informações no arquivo `jd.py`:
   - `CLIENT_ID`: ID da sua aplicação
   - `CLIENT_SECRET`: Secret da sua aplicação
   - `REDIRECT_URI`: URI de redirecionamento (deve ser configurado na aplicação)
   - `SCOPES`: Permissões necessárias

## Uso

Execute o script principal:
```bash
python jd.py
```

O script irá:
1. Abrir o navegador para autenticação
2. Capturar o código de autorização
3. Trocar o código por tokens de acesso
4. Verificar conexões de organização
5. Estar pronto para fazer requisições à API

## Estrutura do Projeto

- `jd.py`: Script principal com implementação OAuth 2.0
- `requirements.txt`: Dependências do projeto
- `.gitignore`: Arquivos ignorados pelo Git
- `README.md`: Este arquivo

## Funcionalidades

- Autenticação OAuth 2.0 com John Deere
- Gerenciamento automático de tokens (refresh)
- Verificação de conexões de organização
- Servidor local para captura de callback
- Tratamento de erros de autenticação

## Segurança

⚠️ **Importante**: Nunca commite credenciais reais no repositório. Use variáveis de ambiente ou arquivos de configuração separados para produção.

## Suporte

Para dúvidas sobre a API da John Deere, consulte a [documentação oficial](https://developer.deere.com). 