-----

# 🏎️ Piloto Automático Híbrido: Lógica Fuzzy + Algoritmos Genéticos

**Para:** Prof. Genaro  
**Aluno:** [Seu Nome Aqui]  
**Disciplina:** [Nome da Matéria]

-----

## 📋 Sobre o Projeto

Este projeto implementa uma simulação de carros autônomos que aprendem a navegar em uma pista complexa (estilo Fórmula 1) sem colidir. A inteligência dos agentes é híbrida, combinando duas grandes áreas da Inteligência Artificial Computacional:

1.  **Lógica Fuzzy (Controlador):** O "cérebro" do carro. O sistema interpreta dados contínuos de 5 sensores de distância e mapeia para ações de direção (-45º a +45º) baseando-se em graus de pertinência, permitindo curvas suaves e decisões mais humanas do que a lógica booleana rígida.
2.  **Algoritmo Genético (Otimizador):** O "treinador". Utiliza princípios da evolução darwiniana para encontrar a melhor combinação de regras para o controlador Fuzzy.

-----

## 🚀 Funcionalidades e Inovações

### 1\. Inteligência Evolutiva Avançada

  * **Recozimento Simulado (Simulated Annealing):** Substituímos a taxa de mutação fixa por uma função de decaimento exponencial. A simulação começa "quente" (25% de mutação) para máxima exploração e "esfria" gradualmente (até 1%) para refinamento fino (fine-tuning) do traçado.
  * **Seleção por Torneio:** Utilizamos o método de torneio ($K=3$) para seleção dos pais, garantindo uma pressão seletiva constante e evitando que indivíduos ruins dominem a roleta por acaso.
  * **Hard Constraints:** Implementação de "morte súbita" para carros que colidem ou andam na contramão, otimizando o processamento e a pressão evolutiva.

### 2\. Visualização e Simulação

  * **Design Vetorial Procedural:** O carro não é uma imagem estática, mas desenhado em tempo real via código (Pygame) utilizando polígonos para simular um chassi estilo F1, com rodas, aerofólio e cockpit.
  * **Pista Complexa:** Traçado não-circular desenhado vetorialmente, contendo retas, curvas fechadas e chicanes (S do Senna).

### 3\. Coleta de Dados Robusta

  * **Sistema de Relatórios Organizados:** Os resultados não são sobrescritos. Uma pasta `relatorios/` é criada automaticamente e cada execução gera arquivos com **ID único** baseado em Data/Hora.
  * **Gravação de Vídeo:** Capacidade de gravar a evolução dos carros em `.mp4` usando OpenCV (opcional).

-----

## 🛠️ Pré-requisitos e Instalação

O projeto foi desenvolvido em **Python 3**. As bibliotecas necessárias são:

  * `pygame` (Motor de simulação visual)
  * `pygad` (Framework de Algoritmo Genético)
  * `scikit-fuzzy` (Lógica Fuzzy)
  * `numpy` (Cálculos matemáticos)
  * `opencv-python` (Gravação de vídeo e processamento de imagem)

### Passo a Passo:

1.  **Clone ou baixe o repositório.**
2.  **Instale as dependências:**
    ```bash
    pip install pygame pygad scikit-fuzzy numpy opencv-python
    ```

-----

## ⚙️ Configuração da Simulação

No início do arquivo `main.py`, existe um dicionário `CONFIG` onde é possível ajustar os hiperparâmetros do experimento:

```python
CONFIG = {
    'FPS': 0,                   # 0 = Velocidade máxima (Treino), 60 = Tempo real.
    'POPULATION_SIZE': 90,      # População maior para garantir diversidade.
    
    # Parâmetros Genéticos
    'CONVERGENCE_TARGET': 0.95, # Meta para encerrar o teste (95% de sucesso).
    'INITIAL_MUTATION': 25.0,   # Taxa inicial (Alta temperatura).
    'COOLING_RATE': 0.995,      # Velocidade de resfriamento da mutação.
    
    'RECORD_VIDEO': False,      # Mude para True para gerar MP4.
}
```

-----

## ▶️ Como Executar

Basta rodar o arquivo principal via terminal:

```bash
python main.py
```

**Durante a execução:**

  * Uma janela abrirá mostrando a pista.
  * O HUD no topo exibe: Geração, Carros Vivos, Vencedores e a **Taxa de Mutação Atual**.
  * Para interromper a qualquer momento e salvar o progresso atual, pressione `Ctrl+C` no terminal. O sistema tratará a interrupção e gerará os relatórios.

-----

## 📊 Analisando os Resultados

Ao final da execução, verifique a pasta `relatorios/`. Lá você encontrará arquivos com o padrão `_ANO-MES-DIA_HORA`:

### 1\. `relatorio_FINAL_ID.txt`

Um relatório técnico detalhado contendo:

  * Lista completa dos parâmetros utilizados (Genoma, Seleção, Elitismo).
  * Estatísticas finais (Melhor Fitness, Média).
  * **Linha do Tempo de Eventos:** Log cronológico de quando surgiu o primeiro vencedor, quando a população convergiu, etc.

### 2\. `dados_FINAL_ID.csv`

Arquivo de dados brutos para plotagem de gráficos (Excel/Pandas):

  * Colunas: `Geracao`, `Melhor_Fitness`, `Media_Fitness`, `Vencedores`, `Taxa_Mutacao`.

### 3\. `video_FINAL_ID.mp4`

(Se ativado na config) Um vídeo mostrando visualmente o processo de aprendizado.

-----

## 🧠 Detalhes Técnicos do Modelo

### O Cromossomo

Cada indivíduo possui um genoma de **25 genes** inteiros.

  * **Entrada:** 5 Sensores x 5 Níveis Fuzzy (Muito Perto a Muito Longe).
  * **Saída:** Cada gene representa um índice de ação de direção (ex: 0 = -45º, 2 = Centro, 4 = +45º).

### Função de Fitness (Aptidão)

A função de recompensa foi projetada para evitar "vícios" (local optima):

1.  **Recompensa Principal:** Se completar 2 voltas, ganha 50.000 pontos + bônus pelo tempo economizado.
2.  **Recompensa Secundária:** Se bater, ganha pontos baseados na distância percorrida.
3.  **Penalidade (Kill Switch):** Se tentar andar na contramão ou bater muito cedo, é eliminado e recebe pontuação zerada ou reduzida para não ser selecionado.