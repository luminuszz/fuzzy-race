

# Anotações

 - Ajustando as taxas de Mutação e Elitismo da roleta para seleccionar os parentes cheguei a uma taxa de 66% de convergência (boa) porém apos algumas interações não identifiquei uma melhora e notei que cheguei em um platô
   - Geração: 36
   - Taxa: 15 a 6%
   - População: 90
   - Taxa C = 66%

  - Baseado nisso decidir a algorítimo de escolha para SUS para verificar se o platô se mantinha na mesma circunstância, Percebi uma uniformidade (sem situações extremas na pista) mas em termos de convergência não teve melhora 
    - Geração: 36
    - Taxa: 15 a 6%
    - População: 90
    - Taxa C = 60%

- Comparando os valores, decidi trabalhar numa taxa de mutação dinâmica usando  Recozimento Simulado buscando a saída de ótimos locais mas mantendo o fluxo de convergência crescente 

  (Valores gerados via IA, com alguns ajustes)
  
- **Gen 1:** Mutação ~25% (Caos total, exploração)

- **Gen 100:** Mutação ~15% (Ainda explorando, mas refinando)
    
- **Gen 300:** Mutação ~5% (Focando na performance)
    
- **Gen 500+:** Mutação ~1% (Ajuste de pixels para bater o recorde)

Utilizando o recozimento consegui ótimos resultados com uma taxa de convergência de 70% já na geração 18
	- Geração: 18
    - Taxa: 25% a 1%
    - População: 90
    - Taxa C = 70$


 