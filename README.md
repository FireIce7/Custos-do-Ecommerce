# Sistema de Cálculo de Custos de Produção

Um sistema completo para gerenciamento e cálculo de custos de produção, desenvolvido em Python com Streamlit e Supabase.

## 📋 Funcionalidades

### 🏭 Gestão de Produção
- **Produtos**: Cadastro e gerenciamento de produtos com fórmulas de cálculo personalizadas
- **Variáveis de Custos**: Controle de variáveis utilizadas nos cálculos (matéria-prima, mão de obra, etc.)
- **Categorias**: Organização de produtos e variáveis por categorias
- **Cálculo Automático**: Avaliação automática de fórmulas para determinar custos

### 🧮 Calculadora de Preços
- **Variáveis de Cálculo**: Configuração de parâmetros específicos para cálculos
- **Calculadora Interativa**: Interface para cálculo de custos com diferentes parâmetros
- **Configurações Personalizáveis**: Ajuste de pesos, perdas e outros fatores

## 🚀 Tecnologias Utilizadas

- **Python 3.11+**
- **Streamlit**: Interface web interativa
- **Supabase**: Banco de dados e autenticação
- **PostgreSQL**: Banco de dados relacional

## 📦 Instalação

### Pré-requisitos
- Python 3.11 ou superior
- Conta no Supabase

### Passos de Instalação

1. **Clone o repositório**
   ```bash
   git clone <url-do-repositorio>
   cd custos-producao
   ```

2. **Instale as dependências**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure as variáveis de ambiente**
   
   Crie um arquivo `.env` na raiz do projeto:
   ```env
   SUPABASE_URL=sua_url_do_supabase
   SUPABASE_KEY=sua_chave_anon_do_supabase
   ```

4. **Configure o banco de dados**
   
   Execute os scripts SQL no Supabase para criar as tabelas:
   ```sql
   -- Tabela de categorias
   CREATE TABLE categorias_custos (
       id SERIAL PRIMARY KEY,
       nome TEXT NOT NULL UNIQUE,
       created_at TIMESTAMP DEFAULT NOW(),
       updated_at TIMESTAMP DEFAULT NOW()
   );

   -- Tabela de variáveis de custos
   CREATE TABLE variaveis_custos (
       id SERIAL PRIMARY KEY,
       nome TEXT NOT NULL,
       valor NUMERIC NOT NULL,
       categoria_id INTEGER REFERENCES categorias_custos(id),
       created_at TIMESTAMP DEFAULT NOW(),
       updated_at TIMESTAMP DEFAULT NOW()
   );

   -- Tabela de produtos
   CREATE TABLE produtos_custos (
       id SERIAL PRIMARY KEY,
       nome TEXT NOT NULL,
       formula TEXT,
       categoria_id INTEGER REFERENCES categorias_custos(id),
       created_at TIMESTAMP DEFAULT NOW(),
       updated_at TIMESTAMP DEFAULT NOW()
   );

   -- Tabela de variáveis de cálculo
   CREATE TABLE variaveis_calc (
       id SERIAL PRIMARY KEY,
       nome TEXT NOT NULL UNIQUE,
       valor NUMERIC NOT NULL,
       created_at TIMESTAMP DEFAULT NOW(),
       updated_at TIMESTAMP DEFAULT NOW()
   );
   ```

5. **Execute a aplicação**
   ```bash
   streamlit run main.py
   ```

## 🏗️ Estrutura do Projeto

```
├── main.py                 # Arquivo principal da aplicação Streamlit
├── producao.py            # Módulo de gestão de produção
├── calculadora.py         # Módulo da calculadora de preços
├── supabase_db.py         # Configuração do cliente Supabase
├── textos.py              # Textos e labels da interface
├── requirements.txt       # Dependências do projeto
└── README.md             # Este arquivo
```

### Descrição dos Módulos

#### `producao.py`
- Funções CRUD para produtos, variáveis e categorias
- Interface Streamlit para gestão de produção
- Validações de entrada e tratamento de erros

#### `calculadora.py`
- Funções de cálculo de custos
- Interface da calculadora de preços
- Gestão de variáveis de cálculo

#### `supabase_db.py`
- Cliente configurado do Supabase
- Gerenciamento de conexão com o banco de dados

#### `textos.py`
- Centralização de todos os textos da interface
- Facilita manutenção e internacionalização

## 💡 Como Usar

### 1. Gestão de Categorias
- Acesse "Gerenciar Categorias" no menu principal
- Adicione, edite ou remova categorias para organizar seus dados

### 2. Cadastro de Variáveis
- Vá para "Variáveis de Custos"
- Cadastre variáveis como preços de matéria-prima, custos de mão de obra, etc.
- Associe variáveis às categorias apropriadas

### 3. Cadastro de Produtos
- Acesse "Produtos"
- Cadastre produtos com suas respectivas fórmulas de cálculo
- Use nomes de variáveis nas fórmulas (ex: `preco_material * quantidade + mao_obra`)

### 4. Calculadora de Preços
- Use a calculadora para cálculos específicos
- Configure variáveis de cálculo conforme necessário
- Obtenha resultados instantâneos

## 🔧 Configuração Avançada

### Fórmulas de Cálculo
As fórmulas suportam:
- Operações matemáticas básicas (`+`, `-`, `*`, `/`)
- Parênteses para precedência
- Nomes de variáveis cadastradas no sistema
- Funções matemáticas básicas

Exemplo de fórmula:
```
(preco_material * quantidade) + (mao_obra * horas) + overhead
```

### Variáveis de Cálculo
Variáveis específicas para a calculadora:
- `peso_50x50`, `peso_30x30`, `peso_25x25`: Pesos das placas
- `perda_50x50`, `perda_30x30`, `perda_25x25`: Percentuais de perda

## 🔒 Segurança

### Configuração Atual
- Utiliza chave `service_role` do Supabase (apenas para desenvolvimento)
- **IMPORTANTE**: Para produção, implemente Row Level Security (RLS)

### Preparação para Produção
1. **Ative RLS nas tabelas**
2. **Adicione coluna `user_id`** em todas as tabelas
3. **Crie políticas de segurança**
4. **Use chave `anon`** do Supabase
5. **Implemente sistema de autenticação**

## 🚧 Próximos Passos

### Sistema de Login
- [ ] Implementar autenticação com Supabase Auth
- [ ] Configurar Row Level Security (RLS)
- [ ] Adicionar `user_id` nas tabelas
- [ ] Criar políticas de acesso por usuário

### Melhorias Futuras
- [ ] Relatórios e dashboards
- [ ] Exportação de dados
- [ ] API REST
- [ ] Testes automatizados
- [ ] Deploy automatizado

## 🤝 Contribuição

1. Faça um fork do projeto
2. Crie uma branch para sua feature (`git checkout -b feature/AmazingFeature`)
3. Commit suas mudanças (`git commit -m 'Add some AmazingFeature'`)
4. Push para a branch (`git push origin feature/AmazingFeature`)
5. Abra um Pull Request

## 📝 Licença

Este projeto está sob a licença MIT. Veja o arquivo `LICENSE` para mais detalhes.

## 📞 Suporte

Para suporte e dúvidas:
- Abra uma issue no GitHub
- Entre em contato através do email: [seu-email@exemplo.com]

## 🏆 Reconhecimentos

- [Streamlit](https://streamlit.io/) - Framework web para Python
- [Supabase](https://supabase.com/) - Backend as a Service
- [PostgreSQL](https://www.postgresql.org/) - Sistema de banco de dados

---

**Desenvolvido com ❤️ para otimizar o cálculo de custos de produção**


