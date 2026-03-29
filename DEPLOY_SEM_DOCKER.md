# Deploy sem Docker

Esta versão do projeto foi preparada para subir sem Docker usando **Flask + Gunicorn**.

## Arquivos adicionados
- `Procfile`
- `runtime.txt`
- `render.yaml`

## Alterações importantes
- `opencv-python` foi trocado por `opencv-python-headless`, que costuma funcionar melhor em servidor.
- O app agora cria automaticamente:
  - pasta do banco
  - pasta de uploads
  - tabelas do SQLite na primeira inicialização

## Hospedagem recomendada
### 1. Render
Boa para apresentação e fácil de conectar ao GitHub.

#### Passos
1. Suba este projeto para um repositório no GitHub.
2. No Render, clique em **New +** > **Web Service**.
3. Conecte o repositório.
4. Configure:
   - **Environment**: `Python`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn run:app`
5. Em **Environment Variables**, defina:
   - `SECRET_KEY` = uma chave forte
   - `DATABASE_PATH` = `/var/data/evento.db`
   - `UPLOAD_FOLDER` = `/var/data/uploads/fotos`
   - `MAX_CONTENT_LENGTH` = `5242880`
6. Adicione um **Persistent Disk** montado em `/var/data`.

> Sem o disco persistente, o banco SQLite e as fotos podem ser perdidos após reinício ou novo deploy.

### 2. Railway
Também funciona bem sem Docker.

#### Passos
1. Suba este projeto para o GitHub.
2. No Railway, escolha **New Project** > **Deploy from GitHub repo**.
3. Nas variáveis de ambiente, defina:
   - `SECRET_KEY`
   - `DATABASE_PATH=/data/evento.db`
   - `UPLOAD_FOLDER=/data/uploads/fotos`
   - `MAX_CONTENT_LENGTH=5242880`
4. Crie um **Volume** e monte em `/data`.
5. Configure o start command como:
   - `gunicorn run:app`

## Teste local antes de subir
```bash
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# ou .venv\Scripts\activate no Windows
pip install -r requirements.txt
python run.py
```

## Observações importantes
- A câmera no navegador precisa de **HTTPS** em celular e navegadores modernos.
- Para trabalho acadêmico, SQLite atende bem.
- Para uso real em produção, o ideal seria migrar depois para PostgreSQL e armazenamento externo de imagens.
