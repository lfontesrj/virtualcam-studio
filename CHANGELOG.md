# Changelog

Todas as mudanças notáveis deste projeto serão documentadas neste arquivo.

## [1.0.0] - 2026-02-09

### Adicionado

- Câmera virtual compatível com Teams, Zoom, Google Meet e outros aplicativos.
- Motor de composição de vídeo com sistema de camadas (webcam, template, ticker, contador, indicadores).
- Quatro templates de overlay prontos: Telejornal Clássico, Corporativo Moderno, Minimalista e Esportivo.
- Ticker de texto rolante no rodapé, alimentado por arquivo `.txt`.
- Contador regressivo configurável com efeito de flash nos últimos 30 segundos.
- Indicadores em tempo real com suporte a `.txt` e `.json` e recarga automática.
- Interface gráfica de controle com CustomTkinter (leve e moderna).
- Assistente de primeira execução com verificação automática do driver.
- Instalador plug-and-play com Inno Setup (Next > Next > Finish).
- Pipeline de CI/CD com GitHub Actions para build automático do instalador.
- Suporte a templates customizados (PNG com transparência).
- Persistência de configurações entre sessões.

### Otimizações

- Interface gráfica: PyQt5 (~80 MB) substituído por CustomTkinter (~5 MB).
- Processamento de vídeo: opencv-python (~80 MB) substituído por opencv-python-headless (~35 MB).
- Compilação com PyInstaller usando strip, UPX e exclusões agressivas.
- Tamanho total instalado reduzido de ~720 MB para ~60-70 MB (redução de ~91%).
