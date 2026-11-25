# 14. Cabeçalho e rodapé: começo e fim da história

O cabeçalho é a capa. O rodapé é o último capítulo. Nenhum dos dois é "o padrão que todo site tem".

## Cabeçalho

### O que ele precisa responder em 1 segundo
1. Onde estou (marca ou nome do negócio, legível)?
2. Como faço a ação principal agora (o CTA, ou telefone/WhatsApp em negócio local)?

O resto é opcional. Página de venda de uma página só muitas vezes **não precisa de menu**: cada link de menu é uma saída do funil (Hick).

### Escolha o comportamento e escreva o porquê

| Comportamento | Como | Quando |
|---|---|---|
| **Some ao descer, volta ao subir** | `transform: translateY(-100%)` ao rolar para baixo, volta ao rolar para cima (calcular a direção com `requestAnimationFrame`, sem evento por pixel) | página longa de leitura; devolve tela no celular |
| **Encolhe** | 72px → 56px depois da primeira dobra, a marca vira só o símbolo | marca forte que precisa ficar presente |
| **Vira barra de ação** | depois do hero, o cabeçalho mostra só o CTA (e o preço, se for venda direta) | landing de venda direta |
| **Mora embaixo no celular** | navegação ou CTA numa barra inferior fixa (área do polegar, Fitts) | negócio local, sistema, público idoso |
| **Estático, rola junto** | sem fixar nada | página curta (≤ 3 telas) ou editorial |
| **Transparente sobre o hero → sólido** | fundo aparece depois da primeira dobra | hero com foto ou cena forte; o texto do cabeçalho precisa de contraste nos dois estados |

### Regras
- Altura no celular: 56 a 64px. Fixo que ocupa mais de 12% da tela (77px a 640) rouba leitura.
- No celular, **nunca** esconder o CTA principal dentro do menu. Se houver menu, o CTA fica fora dele.
- Menu hambúrguer: só se houver mais de 4 destinos. Para público idoso, prefira palavras visíveis ("Serviços · Preços · Onde fica") em linha rolável ou na barra inferior.
- Menu aberto: ocupa a tela, links com o alvo do público, fecha com Esc e com botão escrito "Fechar", foco preso dentro enquanto aberto.
- Link de âncora com `scroll-margin-top` igual à altura do cabeçalho fixo, senão o título some atrás dele.
- O cabeçalho usa os mesmos tokens do resto. Cabeçalho com fonte, espaço ou acabamento diferente rebaixa a página inteira.

## Rodapé

### O rodapé é o fim da história, não a lixeira de links
Quem chega ao rodapé leu tudo e ainda não agiu. Ou está quase convencido, ou procura uma informação prática. O rodapé atende os dois.

### Estrutura em três camadas
1. **Última chamada:** a chamada final se funde com o rodapé (costura de sobreposição ou de forma). Uma frase, o CTA e o redutor de risco.
2. **O prático:** o que a pessoa precisa para agir ou confiar. Negócio local: endereço com rota, horário (com "aberto agora" calculado), telefone escrito por extenso, WhatsApp. Produto: garantia, formas de pagamento, suporte. Profissional regulado: registro (CRM, OAB, CREA, CRO), responsável técnico.
3. **O legal e o mapa:** CNPJ, política de privacidade, termos, créditos de imagem, no menor peso visual permitido (ainda no mínimo de fonte e contraste do público).

### O rodapé conversa com a metáfora
| Nicho | O rodapé vira |
|---|---|
| Engenharia, arquitetura | o **carimbo** da prancha: responsável técnico, CREA/CAU, escala, data, endereço, em grade de carimbo |
| Restaurante, confeitaria | a **comanda/recibo**: endereço, horário e telefone em linhas pontilhadas como itens, "total" = o CTA |
| Saúde | o **receituário**: nome, registro, endereço da clínica, horário de atendimento |
| Barbearia | a **placa da porta**: horário de funcionamento como placa "aberto/fechado", endereço, telefone |
| Turismo | o **canhoto do bilhete**: picote separando o CTA dos dados |
| SaaS | o **terminal/estado do sistema**: status, versão, links de documentação |

### Regras
- Nada de 40 links em 5 colunas. Se a página é uma só, o rodapé tem no máximo 6 links.
- Telefone e endereço são texto real e clicáveis (`tel:`, link de rota), não imagem.
- Ano do copyright é a menor coisa do rodapé, não a primeira.
- No celular, as camadas empilham na ordem: chamada → prático → legal.
- Se houver barra fixa inferior no celular, o rodapé ganha `padding-bottom` da altura dela.
