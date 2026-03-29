# Evento Face Access - SQLite

Projeto acadêmico em Flask + SQLite para controle de acesso com reconhecimento facial simples.

## Como ficou a estrutura

- `/cadastro`: página separada para cadastro
- `/verificacao`: página separada para verificação
- no cadastro, a câmera fica aberta e a foto é tirada automaticamente quando o botão **Cadastrar** é clicado
- na verificação, existe apenas a câmera e o botão para conferir se a pessoa está cadastrada ou não

## Fluxo

### 1. Cadastro
A pessoa preenche:
- nome
- email
- CPF
- telefone

Depois fica em frente à câmera. Quando clicar em **Cadastrar**, o sistema captura a foto naquele momento e salva no banco.

### 2. Verificação
Na entrada do evento, abre-se a página `/verificacao`.
A câmera captura a imagem no clique do botão **Verificar cadastro** e compara com as fotos já cadastradas.

## Como rodar

```bash
python -m venv .venv
.venv\Scripts\activate # no Windows
pip install -r requirements.txt
cp .env.example .env
python scripts/create_tables.py
python run.py
```

Abra no navegador:
- `http://127.0.0.1:5000/cadastro`
- `http://127.0.0.1:5000/verificacao`

