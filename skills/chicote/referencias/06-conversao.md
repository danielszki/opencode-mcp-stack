# 6. Conversão: a ação mais fácil da tela

## O CTA principal

- **Um só.** Marcado com `data-cta="principal"`. É o maior peso da primeira dobra junto com a frase do hero.
- **Visível sem rolar a 360×640.** Portão medido pela chicotada.
- **Volta a cada ~1,5 tela** de rolagem no celular, ou mora numa barra fixa embaixo.
- **Texto = o que acontece**: "Chamar no WhatsApp", "Agendar avaliação grátis", "Ver meu site pronto". Opcionalmente com redutor de risco embaixo, pequeno: "Resposta em até 10 min · sem compromisso".
- Altura mínima: 48px (geral), 56px (idoso). Largura total no celular.
- O secundário tem contorno, não preenchimento, e nunca disputa com o principal.

## Contato para negócio local

Quem chega pelo Google Maps quer três coisas em segundos: **o que faz, quanto custa mais ou menos, como falar**. Então:
- WhatsApp com mensagem pronta (`https://wa.me/55DDDNUMERO?text=...`).
- Telefone clicável (`tel:+55...`), escrito por extenso para quem prefere ligar.
- Endereço com link de rota e horário de funcionamento visível.
- Dados estruturados `LocalBusiness` (ver `09-desempenho-seo.md`).

## Formulário

Cada campo é um degrau. Hick e Hormozi concordam: **menos campos, mais conversão**.

- Peça só o que é necessário **para a próxima ação**, não para o CRM ideal. Orçamento: nome + WhatsApp + uma pergunta. O resto vem na conversa.
- Uma coluna. Rótulo visível em cima do campo. Erro escrito ao lado do campo, dizendo como corrigir.
- Teclado certo: `type="email"`, `type="tel"`, `inputmode="numeric"`, `autocomplete` em todos.
- Botão de envio com o resultado: "Receber meu orçamento", nunca "Enviar".
- Justifique cada campo obrigatório no roteiro. Sem justificativa, ele vira opcional ou sai.

## Cadastro e onboarding (lições do Garimpo e da Korely)

- **Só o essencial é obrigatório.** Na Korely, só o nome (e o e-mail no Pix). No Garimpo, a conta e mais nada: checkout, WhatsApp, Rastro e e-mail têm "pular por agora".
- **Todo passo tem "fazer depois".** Ninguém fica preso numa tela de configuração.
- **Um passo por tela, com o progresso visível** ("Passo 2 de 4") e um caminho para voltar.
- **Testa na hora.** Colou uma chave? O sistema testa e mostra o resultado na mesma tela ("Conectado ✓"), não depois de três telas.
- **Valor antes do esforço.** Mostre a coisa funcionando (prévia, demonstração com a marca da pessoa) antes de pedir dado.
- Conte as telas e os campos do fluxo inteiro e escreva no roteiro. Meta: diminuir os dois a cada versão.

## Sistemas e painéis

- **A moldura é igual em toda tela**: sobrelinha pequena, título grande com ponto final, uma linha de subtítulo, ações à direita (descem no celular).
- **O miolo é diferente em cada tela**: cada tela tem uma estrutura dominante que diz o que ela é (número gigante, calendário, quadro, linha do tempo, conversa, prontuário). Nunca toda tela virando "faixa de KPIs + tabela".
- **A barra lateral está no mesmo nível de acabamento do resto**: mesma tipografia, mesma grade de espaçamento, mesmo cuidado de estado ativo, contador e foco. Barra lateral feia rebaixa o produto inteiro.
- Navegação com no máximo 7 itens por grupo, agrupados por intenção (operação, material, dinheiro, sistema).
- Estado vazio sempre com uma ação ("Nenhum negócio ainda. Buscar no Maps").
- Número sempre `tabular-nums`, alinhado à direita em tabela.
- Ação destrutiva pede confirmação na própria linha (primeiro clique arma, segundo executa), nunca `window.confirm`.

## Preço e oferta

- Pilha de valor primeiro (o que vem, o que resolve cada item), preço depois.
- Âncora honesta: compare com o custo real da alternativa (contratar, fazer sozinho, perder o cliente), não com um "de R$ 997" inventado.
- Garantia escrita em uma frase, com prazo.
- Sem urgência falsa (contagem regressiva que reinicia, "últimas vagas" eternas).
