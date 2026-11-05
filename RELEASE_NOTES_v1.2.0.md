# 🚀 Release v1.2.0 — Smart Perceptual Keyframes Engine

> **Universal Multimodal Reverse-Engineering Pipeline for AI Agents & Developers**  
> *Mantido por 4Pixel Tech (`@4pixeltechBR`)*

---

### 🌟 Destaques desta Versão

A versão **v1.2.0** resolve o maior gargalo na decupagem de vídeos longos, tutoriais técnicos e palestras: a **amostragem cega equidistante**. Em vez de fatiar o vídeo uniformemente ($\Delta t = \text{duração}/N$), o motor agora implementa uma pipeline inteligente de **Visão Computacional Perceptual em 2 estágios**.

---

### 🧠 Novas Funcionalidades & Melhorias de Engenharia

1. **Scan 1-FPS em Memória RAM com Crop Central de 80% (`ROI`):**
   * O FFmpeg realiza o streaming de 1 frame por segundo diretamente em RAM (`rawvideo` 64x64 gray — apenas 4 KB por segundo).
   * **Zero gravação inútil no SSD**: economiza milhares de I/O por hora de vídeo.
   * **Máscara Central (80% ROI):** Descarta as bordas e cantos do vídeo, eliminando falsos positivos gerados por webcams (*Picture-in-Picture*) e barras do sistema operacional.

2. **Perceptual dHash de 256 bits (`16x16`) + Detecção de Bordas Espaciais:**
   * Enquanto hashes padrão de 64 bits (8x8) ignoram edições sutis em temas escuros (VS Code), o algoritmo **`dHash` de 256 bits** captura trocas de abas, funções novas e alterações de linhas de código.
   * Cálculo contínuo de **densidade de bordas (`edge_density`)**, classificando a tela automaticamente em:
     * `Alta Densidade (Código / Diagrama / Terminal)`
     * `Média Densidade (Slide / Interface / Browser)`
     * `Baixa Densidade (Apresentador / Transição / B-Roll)`

3. **Estabilização por Dwell Time (`Anti-Blur`) & Deduplicação Cruzada:**
   * Aguarda a tela se estabilizar após animações de rolagem ou transição (`>= 2s` de platô) e captura o segundo de **maior nitidez** dentro da janela.
   * **Deduplicação A → B → A:** Se o autor alterna da tela de código para a câmera e depois volta para a mesma tela, o motor funde o tempo de permanência sem duplicar o frame.
   * **Orçamento Inteligente (`--frames 36` ou `--frames 0` para ilimitado):** Prioriza telas pela métrica $\text{Importância} = \log_2(1 + \text{Dwell Time}) \times \text{Densidade}$.

4. **Novo Relatório Visual com Janelas de Permanência (`video_report.md`):**
   * Cada frame documenta o intervalo exato em que a tela ficou visível (ex: `04:12 → 05:30 | 78s em tela`), o *Edge Score* e correlaciona toda a fala do autor durante a permanência daquela cena.

---

### 📦 Novas Flags de CLI Adicionadas

| Flag | Tipo | Padrão | Descrição |
| :--- | :---: | :---: | :--- |
| `--frame-mode` | `{smart, uniform}` | `smart` | Alterna entre o novo motor perceptual ou amostragem uniforme legado. |
| `--frames` | Inteiro | `36` | Limite máximo de telas únicas a extrair (`0` = sem limite). |
| `--min-dwell` | Inteiro | `2` | Segundos mínimos de estabilidade para validar uma tela como cena. |
| `--hash-threshold` | Inteiro | `26` | Limiar de distância de Hamming (de 256 bits) para disparar nova cena. |

---

### 🛠️ Commits Incluídos
* `aae5072`: `feat(visual): upgrade to v1.2.0 Smart Perceptual Keyframes (256-bit dHash + 80% ROI + Dwell Stabilization)`
* `aa3ee20`: `docs: update README.md and README_PT.md for v1.2.0 Smart Perceptual Keyframes`
