# VirtualCam Studio

**Câmera virtual profissional com overlays estilo telejornal para Windows 11.**

O VirtualCam Studio cria uma câmera virtual no seu computador que pode ser selecionada no Microsoft Teams, Zoom, Google Meet e outros aplicativos de videoconferência. Ele combina o vídeo da sua webcam real com camadas de overlay profissional, incluindo templates de telejornal, ticker de texto rolante, contador regressivo e indicadores em tempo real.

---

## Funcionalidades

| Funcionalidade | Descrição |
|---|---|
| **Câmera Virtual** | Aparece como dispositivo de vídeo no Windows, compatível com Teams, Zoom, Meet, etc. |
| **Templates de Overlay** | 4 templates prontos (Telejornal, Corporativo, Minimalista, Esportivo) + suporte a imagens customizadas (PNG com transparência) |
| **Ticker de Texto** | Barra de texto rolante no rodapé, alimentada por arquivo `.txt` ou digitação manual |
| **Contador Regressivo** | Timer configurável com posição ajustável e efeito de flash nos últimos 30 segundos |
| **Indicadores em Tempo Real** | Exibe dados de arquivo `.txt` ou `.json` com recarga automática |
| **Interface de Controle** | Painel completo com abas para configurar cada funcionalidade |
| **Persistência** | Configurações salvas automaticamente entre sessões |
| **Instalador Plug-and-Play** | Instalação tipo "Next > Next > Finish", sem conhecimento técnico |

---

## Requisitos de Sistema

| Requisito | Especificação |
|---|---|
| **Sistema Operacional** | Windows 11 (64-bit) |
| **Espaço em Disco** | ~60-70 MB (sem OBS) ou ~560 MB (com OBS embutido) |
| **Webcam** | Qualquer webcam USB ou integrada |
| **Driver Virtual** | OBS Studio (para o driver de câmera virtual) |
| **RAM** | 4 GB mínimo recomendado |

---

## Instalação para Usuário Final

A instalação é do tipo **"Next > Next > Finish"** — nenhum conhecimento técnico é necessário.

1. Execute o arquivo `VirtualCamStudio_Setup_v1.0.0.exe`.
2. Siga as telas do assistente de instalação.
3. O instalador cuida de tudo automaticamente, incluindo o registro do driver de câmera virtual.
4. Ao finalizar, o VirtualCam Studio será aberto automaticamente.

Se o OBS Studio não estiver instalado, o instalador oferecerá a opção de instalá-lo automaticamente (necessário para o driver da câmera virtual).

---

## Instalação para Desenvolvimento

Para quem deseja modificar o código-fonte ou contribuir com o projeto.

### Pré-requisitos

O único pré-requisito é o **Python 3.11+** instalado no sistema.

### Instalação Rápida

```batch
install_dev.bat
```

Isso cria um ambiente virtual, instala as dependências e gera os templates.

### Instalação Manual

```batch
python -m venv venv
venv\Scripts\activate.bat
pip install -r requirements.txt
python src\template_generator.py
python src\main.py
```

### Dependências (Otimizadas)

| Pacote | Tamanho | Função |
|---|---|---|
| `opencv-python-headless` | ~35 MB | Processamento de vídeo (sem GUI Qt) |
| `numpy` | ~30 MB | Computação numérica |
| `customtkinter` | ~5 MB | Interface gráfica moderna e leve |
| `Pillow` | ~10 MB | Manipulação de imagens para preview |
| `pyvirtualcam` | ~2 MB | Saída para câmera virtual |
| **Total** | **~50 MB** | |

---

## Compilação do Instalador

Para gerar o instalador distribuível para usuários finais.

### Pré-requisitos de Build

| Ferramenta | Download | Obrigatório |
|---|---|---|
| Python 3.11+ | [python.org](https://python.org) | Sim |
| PyInstaller | `pip install pyinstaller` | Sim |
| Inno Setup 6 | [jrsoftware.org](https://jrsoftware.org/isinfo.php) | Sim (para o instalador) |
| UPX | [github.com/upx/upx](https://github.com/upx/upx/releases) | Opcional (reduz ~30%) |

### Build Completo

```batch
build_installer.bat
```

O script realiza automaticamente: instalação de dependências, geração de templates, compilação com PyInstaller (com strip e UPX), e geração do instalador com Inno Setup.

### Tamanhos Estimados do Build

| Cenário | Instalador (download) | Instalado em disco |
|---|---|---|
| **Sem OBS embutido** | ~30-40 MB | ~60-70 MB |
| **Com OBS embutido** | ~230 MB | ~560 MB |

Para incluir o OBS no instalador, baixe o instalador do OBS de [obsproject.com](https://obsproject.com/download) e coloque como `installer/OBS-Studio-Full-Installer-x64.exe`.

---

## Build Automático com GitHub Actions (CI/CD)

O projeto inclui um pipeline de CI/CD que **compila automaticamente o instalador `.exe`** usando GitHub Actions. Com isso, você não precisa ter PyInstaller, Inno Setup ou UPX instalados localmente.

### Como funciona

O workflow é acionado automaticamente em três situações:

| Trigger | Ação | Resultado |
|---|---|---|
| **Push na branch `main`** | Build automático | Instalador disponível como Artifact no GitHub Actions |
| **Criação de tag `v*`** (ex: `v1.0.0`) | Build + Release | Instalador publicado como Release no GitHub |
| **Manual (workflow_dispatch)** | Build sob demanda | Permite escolher se inclui o OBS no bundle |

### Passo a passo para gerar o instalador

1. Crie um repositório no GitHub e faça push do código:

```bash
cd virtualcam-studio
git init
git add .
git commit -m "Initial commit - VirtualCam Studio v1.0.0"
git remote add origin https://github.com/SEU-USUARIO/virtualcam-studio.git
git push -u origin main
```

2. O GitHub Actions iniciará o build automaticamente. Acompanhe em **Actions** no repositório.

3. Após o build (5-10 minutos), o instalador estará disponível:
   - Na aba **Actions** > clique no workflow > **Artifacts** > `VirtualCamStudio-Installer`
   - Ou, para criar um Release público, crie uma tag:

```bash
git tag v1.0.0
git push origin v1.0.0
```

4. O Release será criado automaticamente na aba **Releases** do repositório, com o instalador `.exe` pronto para download.

### Build manual com opção de incluir OBS

Vá em **Actions** > **Build Windows Installer** > **Run workflow** e selecione `true` em "Incluir OBS Studio" para gerar o instalador all-in-one (~230 MB) que não requer nenhuma dependência externa.

---

## Estrutura do Projeto

```
virtualcam-studio/
├── src/                          # Código-fonte
│   ├── main.py                   # Ponto de entrada
│   ├── main_window.py            # Interface gráfica (CustomTkinter)
│   ├── compositor.py             # Motor de composição de vídeo
│   ├── camera_manager.py         # Captura de webcam e câmera virtual
│   ├── settings.py               # Gerenciamento de configurações
│   ├── first_run.py              # Setup de primeira execução
│   └── template_generator.py     # Gerador de templates
├── assets/                       # Recursos
│   ├── templates/                # Templates PNG de overlay
│   ├── sample_ticker.txt         # Exemplo de ticker
│   ├── sample_indicators.txt     # Exemplo de indicadores (texto)
│   └── sample_indicators.json    # Exemplo de indicadores (JSON)
├── drivers/                      # Scripts de driver
│   ├── install_virtualcam.bat    # Registrar driver
│   ├── uninstall_virtualcam.bat  # Desregistrar driver
│   └── install_obs_silent.ps1    # Instalação silenciosa do OBS
├── installer/                    # Inno Setup
│   └── setup_allinone.iss        # Script do instalador
├── .github/workflows/            # CI/CD
│   └── build-installer.yml       # GitHub Actions workflow
├── requirements.txt              # Dependências Python
├── virtualcam_studio.spec        # PyInstaller spec
├── build_installer.bat           # Script de build local
├── install_dev.bat               # Instalação para desenvolvimento
├── run.bat                       # Execução rápida
├── CHANGELOG.md                  # Histórico de versões
├── .gitignore                    # Exclusões do Git
└── LICENSE                       # Licença GPL-2.0
```

---

## Uso

### Primeiro Uso

1. Abra o **VirtualCam Studio**.
2. Se for a primeira vez, o programa verificará se o driver de câmera virtual está disponível.
3. Clique em **"Iniciar Transmissão"** no painel principal.
4. No seu aplicativo de videoconferência (Teams, Zoom, Meet), selecione **"OBS Virtual Camera"** como câmera.

### Configurando Overlays

Na barra lateral direita, use as abas para configurar cada funcionalidade:

**Aba "Template"** — Selecione um template pronto ou carregue uma imagem PNG customizada. Ajuste a opacidade com o slider.

**Aba "Ticker"** — Ative o ticker e carregue um arquivo `.txt` com o texto desejado (um item por linha). Ajuste a velocidade de rolagem.

**Aba "Contador"** — Ative o contador, defina a duração em minutos e a posição na tela. Use os botões Iniciar, Pausar e Resetar.

**Aba "Indicadores"** — Carregue um arquivo `.txt` (formato `LABEL: VALOR`) ou `.json` com os indicadores. Ative a recarga automática para atualização em tempo real.

### Formato dos Arquivos de Dados

**Ticker (`.txt`):**
```
Primeira notícia ou informação
Segunda notícia ou informação
Terceira notícia ou informação
```

**Indicadores (`.txt`):**
```
Vendas: R$ 1.250.000
Meta: 85%
Clientes: 342
```

**Indicadores (`.json`):**
```json
[
  {"label": "Vendas", "value": "R$ 1.250.000", "color": [46, 204, 113]},
  {"label": "Meta", "value": "85%", "color": [255, 255, 255]},
  {"label": "Clientes", "value": "342", "color": [52, 152, 219]}
]
```

---

## Otimizações Realizadas

A versão otimizada reduziu significativamente o tamanho do software sem perder funcionalidades.

| Componente | Antes | Depois | Economia |
|---|---|---|---|
| Interface gráfica | PyQt5 (~80 MB) | CustomTkinter (~5 MB) | 75 MB |
| Processamento de vídeo | opencv-python (~80 MB) | opencv-python-headless (~35 MB) | 45 MB |
| Renderização de texto | Pillow obrigatório | OpenCV nativo + Pillow opcional | ~5 MB |
| Compilação | PyInstaller padrão | PyInstaller + strip + UPX | ~30% |
| **Total instalado** | **~720 MB** | **~60-70 MB** | **~90%** |

---

## Licença

Este projeto é distribuído sob a licença **GPL-2.0**, em conformidade com a licença das bibliotecas `pyvirtualcam` e `OBS Studio` das quais depende. Consulte o arquivo [LICENSE](LICENSE) para mais detalhes.
