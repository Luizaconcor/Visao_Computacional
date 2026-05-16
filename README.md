# Controle Facial

Projeto acadêmico em Flask + SQLite para controle de acesso com reconhecimento facial usando **dlib**.

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
A câmera captura a imagem no clique do botão **Verificar cadastro** e compara com as fotos já cadastradas usando descritores faciais de 128 dimensões gerados pelo dlib.

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

## Método dlib

O arquivo principal alterado foi:

- `app/services/verification_service.py`

A verificação agora funciona assim:

1. O dlib detecta o rosto principal na imagem.
2. O modelo de landmarks de 5 pontos alinha o rosto.
3. O modelo ResNet do dlib gera um descritor facial de 128 dimensões.
4. O sistema calcula a distância euclidiana entre os descritores.
5. Se a distância for menor ou igual a `0.60`, a pessoa é considerada correspondente.

Os modelos `.dat` são fornecidos automaticamente pela dependência `face-recognition-models`, então não é necessário baixar manualmente os arquivos do dlib.

Se estiver no Windows e a instalação do `dlib` falhar, instale o CMake e o Visual Studio Build Tools antes de rodar `pip install -r requirements.txt`.

## Relatórios

Acesse também:
- `http://127.0.0.1:5000/relatorios/logs`

Nesta rota, o gráfico de resultados da tabela `logs_acesso` é regenerado automaticamente sempre que a página é aberta.