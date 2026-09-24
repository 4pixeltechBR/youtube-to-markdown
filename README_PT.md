# youtube-to-markdown (yt2md)

[![License: MIT](https://img.shields.io/badge/Licen%C3%A7a-MIT-blue.svg)](LICENSE)
[![Python: 3.10+](https://img.shields.io/badge/Python-3.10+-brightgreen.svg)](https://python.org)
[![Whisper: Groq Turbo](https://img.shields.io/badge/Whisper-Groq%20v3%20Turbo-orange.svg)](https://console.groq.com)
[![Harness: Agent--Native](https://img.shields.io/badge/AI%20Harness-Pronto-purple.svg)](SKILL.md)
[![Obsidian Canvas](https://img.shields.io/badge/Obsidian-Canvas%20Suportado-purple)](https://obsidian.md)
[![English](https://img.shields.io/badge/Documentation-English-blue)](README.md)

**Motor universal de engenharia reversa multimodal para desenvolvedores e agentes de IA.**  
Transforme vídeos do YouTube, playlists inteiras, TikTok, Instagram Reels, vídeos do X (Twitter) e podcasts em Markdown estruturado, transcrições com legendas nativas (CC) sem gastar API ou Whisper neural, decupagem visual de 16 quadros (frames), comentários da comunidade e mapas mentais interativos em formato Obsidian Canvas e Mermaid.

> **Nativo para Harness de IA:** Sem interface web pesada (zero Streamlit/Gradio). Projetado para rodar direto de dentro do **Claude Code, Antigravity, OpenAI Codex, OpenCode, MiniMax Code, Cursor e Aider** — ou via linha de comando no terminal.

---

## ⚡ Diferenciais do Projeto

A maioria das ferramentas do mercado apenas cospe textos brutos ou exige interfaces gráficas desconectadas do fluxo de desenvolvimento. O **`youtube-to-markdown` é um pipeline completo de inteligência técnica**:

| Funcionalidade | Ferramentas Tradicionais | `youtube-to-markdown` |
| :--- | :---: | :---: |
| **Download de Legenda Nativa (CC)** | ❌ Força transcrição paga | ✅ **Sim ($0 custo, 0.5s de resposta)** |
| **Fallback Neural Whisper** | ⚠️ Whisper local lento ou caro | ✅ **Groq Whisper v3 Turbo (< 3s)** |
| **Detecção Inteligente de Playlist** | ❌ Baixa tudo ou quebra | ✅ **Pergunta se quer 1 vídeo ou a playlist** |
| **Compressão Extrema de Áudio** | ❌ Sobe arquivos brutos gigantes | ✅ **FFmpeg 16kHz mono 32k (-90% de tamanho)** |
| **Linha do Tempo Visual (16 Frames)** | ❌ Apenas áudio/texto | ✅ **16 quadros sincronizados com o diálogo** |
| **Suporte Nativo a Obsidian Canvas** | ❌ Apenas texto simples | ✅ **Gera `.canvas` JSON nativo + Mermaid `.mmd`** |
| **Extração de Comentários Públicos** | ❌ Exige API Key do Google | ✅ **Integrado direto (Sem API key)** |
| **Compatibilidade com Harness de IA** | ❌ Focado em humanos/web | ✅ **Arquivo `SKILL.md` + saída JSON limpa** |
| **Suporte Multiplataforma** | ❌ Apenas YouTube | ✅ **YouTube, TikTok, IG, X, Podcasts** |

---

## 📂 Ativos Gerados por Execução

Cada conteúdo processado gera uma pasta estruturada pronta para consumo:

```
output/Como Criar um Agente de IA - Fireship/
├── INDEX.md                  # Central de navegação com links clicáveis locais (file:///)
├── transcript.md             # Transcrição completa (blocos de 1 min com timestamp + texto contínuo)
├── video_report.md           # Decupagem visual dos 16 frames com a fala exata do autor
├── STRATEGIES.md             # SOP Operacional, playbook de execução e prompts copiáveis
├── MINDMAP.md                # Mapa mental formatado em Markdown com Mermaid interativo
├── mindmap.canvas            # Canvas nativo do Obsidian (cards coloridos e conectados)
├── mindmap.mmd               # Código Mermaid puro
├── comments.md               # Comentários fixados do autor, discussões e dúvidas da audiência
├── video_info.json           # Metadados completos estruturados
└── frames/                   # 16 imagens JPG em alta resolução
    ├── frame_01_0014s.jpg
    └── ...
```

---

## 📋 Pré-requisitos & Instalação

### 1. Requisitos
- **Python 3.10 ou superior**
- **FFmpeg** (Recomendado no PATH do sistema, ou gerenciado automaticamente pelo `imageio-ffmpeg`)
- **Chave de API da Groq** (Gratuita em [console.groq.com/keys](https://console.groq.com/keys)) — *usada apenas se o vídeo não tiver legendas nativas (CC)!*

### 2. Instalação

Clone o repositório e instale as dependências:

```bash
git clone https://github.com/4pixeltechBR/youtube-to-markdown.git
cd youtube-to-markdown
pip install -r requirements.txt
```

*(Opcional)* Instale localmente como comando de terminal:

```bash
pip install -e .
```

### 3. Configuração de Ambiente

Copie o `.env.example` para `.env` e configure sua chave da Groq:

```bash
cp .env.example .env
```

```env
GROQ_API_KEY=gsk_sua_chave_groq_aqui
# Opcional: Diretório padrão de saída (substitui ./output)
# YT2MD_OUTPUT_DIR=E:/Ideias/
```

---

## 🚀 Como Usar

### 1. Modo Terminal Interativo
Basta passar o link. Se o link contiver tanto o vídeo quanto a playlist (`v=` e `list=`), a ferramenta pergunta o que você deseja fazer:

```bash
python yt2md.py "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
```

```
============================================================
  [?] URL de playlist detectada com um vídeo específico!
      1) Processar APENAS este vídeo (recomendado)
      2) Processar a PLAYLIST INTEIRA em lote
============================================================
  Escolha a opção [1/2, padrão: 1]: 1

  Onde deseja salvar os arquivos?
  Diretório [padrão: ./output/Rick Astley - Never Gonna Give You Up]:
```

### 2. Processamento em Lote de Playlists
Para processar uma playlist completa com criação de sumário mestre (`PLAYLIST_SUMMARY.md`):

```bash
python yt2md.py "https://www.youtube.com/playlist?list=PLxxx" --playlist
```

### 3. Definir Diretório de Saída
Salve diretamente na pasta do seu projeto ou no cofre do Obsidian:

```bash
python yt2md.py "<URL>" -o "E:/Obsidian/Cofre/Pesquisas/"
```

### 4. Modo Rápido Áudio/Texto (Sem baixar vídeo ou frames)
Ideal para podcasts ou palestras longas:

```bash
python yt2md.py "<URL>" --no-frames
```

### 5. Multiplataforma
Funciona com mídias suportadas pelo ecossistema yt-dlp:
```bash
# TikTok
python yt2md.py "https://www.tiktok.com/@usuario/video/123456789"

# Instagram Reels
python yt2md.py "https://www.instagram.com/reel/Cxxxxxxx/"

# Vídeos do X (Twitter)
python yt2md.py "https://x.com/usuario/status/123456789"
```

---

## 🤖 Uso Dentro de Harness de IA (Claude Code, Antigravity, OpenCode, Codex)

O repositório inclui a especificação universal [`SKILL.md`](SKILL.md).

### Para Agentes de IA:
Basta instruir o agente ou rodar com o parâmetro `--json` para receber uma resposta estruturada sem ruído:

```bash
python yt2md.py "<URL>" --json --single-video
```

**Retorno estruturado em JSON:**
```json
{
  "status": "success",
  "title": "Agentes Autônomos em Produção",
  "author": "Tech Lead",
  "output_dir": "E:/Ideias/Agentes Autônomos",
  "index_file": "E:/Ideias/Agentes Autônomos/INDEX.md",
  "inventory": {
    "Transcript (Markdown)": "E:/.../transcript.md",
    "Visual Timeline Report": "E:/.../video_report.md",
    "Operational SOP & Playbook": "E:/.../STRATEGIES.md",
    "Mind Map (Mermaid View)": "E:/.../MINDMAP.md",
    "Obsidian Interactive Canvas": "E:/.../mindmap.canvas",
    "Community Comments & Insights": "E:/.../comments.md"
  }
}
```

---

## 🧠 Integração com Obsidian Canvas

Ao abrir a pasta gerada no [Obsidian](https://obsidian.md), o arquivo `mindmap.canvas` exibe um mapa visual de nós navegável:

```
[ Tópico Central ] ───> [ Pilar 1: Contexto & Problema ] ───> [ Card: Detalhes ]
                   ───> [ Pilar 2: Arquitetura ]        ───> [ Card: Detalhes ]
                   ───> [ Pilar 3: Implementação ]      ───> [ Card: Detalhes ]
                   ───> [ Pilar 4: Entregáveis ]        ───> [ Card: Detalhes ]
```

---

## 🛠️ Tabela de Parâmetros CLI

```
uso: yt2md [-h] [-o OUTPUT] [--playlist] [--single-video] [--no-frames]
           [--no-comments] [--force-whisper] [--groq-key GROQ_KEY]
           [--lang LANG] [--json] [-q] [-v] [url]

argumentos posicionais:
  url                   URL da mídia (YouTube, Playlist, TikTok, IG, X)

opções:
  -h, --help            Exibe mensagem de ajuda
  -o, --output OUTPUT   Diretório de destino customizado
  --playlist            Força o processamento em lote da playlist inteira
  --single-video        Força o processamento apenas do vídeo individual
  --no-frames           Pula o download do vídeo 720p e a extração dos 16 frames
  --no-comments         Pula a extração de comentários públicos
  --force-whisper       Ignora legendas nativas (CC) e força Groq Whisper
  --groq-key KEY        Chave customizada da API da Groq
  --lang LANG           Idiomas preferidos (padrão: 'en,pt')
  --json                Retorna JSON puro no terminal (ideal para agentes)
  -q, --quiet           Modo silencioso (sem banners)
  -v, --version         Exibe versão da ferramenta
```

---

## 📄 Licença

Distribuído sob a licença **MIT**. Veja o arquivo [`LICENSE`](LICENSE) para mais informações.

Desenvolvido por **4Pixel Tech** ([@4pixeltechBR](https://github.com/4pixeltechBR)).
