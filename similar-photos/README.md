# similar-photos

Script CLI + app gráfico Linux que faz o mesmo fluxo:

1. **Gera 3 imagens parecidas** a partir de uma foto  
2. **Busca origem/fóruns** — páginas públicas que hospedam **esse arquivo/quadro** (não identifica pessoas)

## Requisitos

- Linux (testado mentalmente em Ubuntu/Debian)
- Python 3.10+
- `tkinter` (GUI): `sudo apt install python3-tk python3-pil`

```bash
cd similar-photos
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install -e .
```

## CLI

```bash
# 3 parecidas (local PIL; ou OpenAI se OPENAI_API_KEY estiver definida)
similar-photos gen foto.jpg -o ./outputs/foto

# só transforms locais
similar-photos gen foto.jpg --local

# origem / helpers de busca reversa (não inventa URLs)
similar-photos source foto.jpg
similar-photos source foto.jpg --open   # abre TinEye/Yandex/Google no navegador

# os dois
similar-photos run foto.jpg --local

# GUI
similar-photos gui
# ou: python -m similar_photos.gui
```

## OpenAI (opcional)

```bash
export OPENAI_API_KEY=sk-...
similar-photos gen foto.jpg   # tenta variations da API; se falhar, cai no PIL local
```

## O que a busca de origem faz / não faz

- **Faz:** calcula SHA-256, devolve helpers (TinEye, Yandex, Google, Bing) e JSON limpo  
- **Não faz:** inventar links de fórum, rastrear pessoa por rosto/tatuagem, montar dossier  

Engines costumam bloquear upload automatizado; o app abre o caminho manual honesto.

## Estrutura

```
similar-photos/
  similar_photos/
    cli.py      # gen | source | run | gui
    gen.py      # PIL local + OpenAI opcional
    source.py   # relatório de origem
    gui.py      # tkinter
  README.md
  requirements.txt
  pyproject.toml
```
