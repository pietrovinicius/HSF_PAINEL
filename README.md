# HSF Painel - Painel de Enfermagem para Monitoramento de Pacientes

## 📖 Sobre o Projeto

Este projeto é um painel de dados interativo (`dashboard`), construído com **Streamlit** e **Python**, projetado para ser exibido em televisões nas estações de enfermagem do Hospital São Francisco.

O objetivo principal é fornecer à equipe de enfermagem e outros profissionais de saúde uma visão clara, centralizada e em **tempo real** das informações vitais dos pacientes internados. Através dele, a equipe pode consultar rapidamente dados de atendimentos, históricos, alergias, e outros indicadores de cuidado diretamente do leito.

## 🎯 O Problema Resolvido

A principal "dor" que este painel busca resolver é a dependência de processos manuais e demorados, como:

1.  **Otimizar o uso do ERP Tasy:** Reduz a necessidade de múltiplos cliques e buscas no sistema principal para encontrar informações de rotina.
2.  **Eliminar Relatórios Impressos:** Substitui a impressão constante de relatórios em papel, que rapidamente se desatualizam, gerando economia de recursos e garantindo que a equipe sempre acesse a informação mais recente.

Em resumo, o painel digitaliza e agiliza o acesso à informação clínica, permitindo que a equipe foque mais no cuidado ao paciente e menos na busca por dados.

## ✨ Funcionalidades Principais

*   **Visão por Unidade/Andar:** O menu lateral permite que a equipe de enfermagem navegue facilmente entre as diferentes unidades de internação do hospital.
*   **Painel do Paciente:** Cada página exibe um layout claro com os leitos da unidade, mostrando informações essenciais como:
    *   Nome do paciente
    *   Idade e tempo de internação
    *   Diagnósticos principais
*   **Indicadores e Alertas Visuais:** Exibição clara de informações críticas como:
    *   Alergias conhecidas
    *   Risco de queda
    *   Risco de úlcera por pressão (UPP)
    *   Outros indicadores assistenciais relevantes.
*   **Dados em Tempo Real:** O painel se conecta diretamente ao banco de dados Oracle, garantindo que todas as informações exibidas sejam sempre as mais atuais.

## 🛠️ Tecnologias Utilizadas

*   **Linguagem:** Python
*   **Framework Web:** Streamlit
*   **Manipulação de Dados:** Pandas
*   **Banco de Dados:** Oracle (conectado via `oracledb`)

## 🚀 Como Executar o Projeto

Siga os passos abaixo para configurar e executar o projeto em seu ambiente local.

### **Pré-requisitos**

*   Python 3.9+
*   Acesso ao banco de dados Oracle do HSF.

### **1. Clonar o Repositório**

```bash
git clone [URL_DO_SEU_REPOSITORIO_GIT]
cd HSF_PAINEL
```

### **2. Configurar o Ambiente Virtual**

É uma boa prática usar um ambiente virtual para isolar as dependências.

```bash
# Criar o ambiente virtual
python -m venv venv

# Ativar o ambiente (Windows)
.\venv\Scripts\activate

# Ativar o ambiente (Linux/macOS)
source venv/bin/activate
```

### **3. Instalar as Dependências**

Este projeto precisa de um arquivo `requirements.txt` para garantir que todos usem as mesmas versões das bibliotecas. Se ele não existir, crie-o com o comando:
`pip freeze > requirements.txt`

Depois, instale as dependências:

```bash
pip install -r requirements.txt
```

### **4. Configurar as Credenciais do Banco (Segurança)**

Para evitar expor dados sensíveis no código, o Streamlit utiliza um arquivo de "segredos".

1.  Crie o arquivo: `.streamlit/secrets.toml`
2.  Adicione o conteúdo abaixo, substituindo pelas suas credenciais de acesso:

    ```toml
    # .streamlit/secrets.toml
    [db_credentials]
    username = "SEU_USUARIO_DO_BANCO"
    password = "SUA_SENHA_DO_BANCO"
    dsn = "SEU_HOST:PORTA/SERVICE_NAME"
    ```
    *Este arquivo **não deve** ser enviado para o repositório Git por segurança.*

### **5. Executar o Painel**

Com tudo configurado, inicie o aplicativo Streamlit:

```bash
streamlit run inicio.py
```

O painel será aberto automaticamente no seu navegador padrão.

## 📂 Estrutura do Projeto

```
.
├── .streamlit/
│   ├── config.toml      # Configurações de tema e layout do Streamlit
│   └── secrets.toml     # Arquivo de credenciais (NÃO VERSIONAR)
├── Pages/               # Cada arquivo .py aqui vira uma página no menu lateral
│   ├── EMORP_U_I_09_ANDAR.py
│   └── ...
├── inicio.py            # Página inicial do painel
├── requirements.txt     # Lista de dependências do projeto
└── README.md            # Este arquivo de documentação
```
