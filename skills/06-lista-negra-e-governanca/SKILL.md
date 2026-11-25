---
name: 06-lista-negra-e-governanca
description: Define as ordens obrigatórias de governança para qualquer operação comercial multi-canal: Lista Negra de Jargões (35+ termos e clichês banidos com substituição obrigatória), Lista Negra definitiva de contatos (opt-out cross-channel), parâmetros configuráveis da operação, filtro de bots, limites anti-spam e autópsia pós-perda. Use antes de escrever ou enviar qualquer mensagem e após toda conversa encerrada.
---

# 06. Lista Negra, Anti-Jargão e Governança de Operação

Esta skill é o **controle de qualidade e segurança** da operação. Nenhuma abordagem, resposta ou follow-up pode violar as ordens abaixo.

---

## ORDEM DIRETA 1: Lista Negra de Jargões (Execução Obrigatória)

**Instrução ao Agente:**
ANTES de enviar ou exibir qualquer rascunho para o usuário em **WhatsApp, LinkedIn, E-mail ou Direct**, faça uma varredura completa no texto contra a lista negra abaixo.
- Se encontrar **qualquer palavra, variação ou clichê desta lista**, **PARE, CORTE E REESCREVA** em português direto de conversa real entre duas pessoas.
- Nunca entregue texto que pareça copiado de palestra de marketing ou template gringo traduzido.

### Lista Negra Completa (Palavras e Expressões Banidas)

1. **Clichês de Marketing e Consultoria:**
   - `alavancar`, `transformação digital`, `sinergia`, `ecossistema`, `disruptivo`, `escalar resultados`, `virada de chave`, `próximo nível`, `solução inovadora`, `solução completa`, `solução sob medida` (em abertura fria), `parceria estratégica`, `maximizar`, `potencializar`, `otimização 360`, `alta performance`, `jornada do cliente`, `agregar valor`, `dor latente`, `ticket médio` (falando com o cliente).
2. **Clichês de E-mail Frio / SDR Robótico:**
   - `espero que este e-mail o encontre bem`, `espero que esteja tudo ótimo por aí`, `gostaria de apresentar`, `vim através deste`, `sem compromisso algum, apenas 15 minutinhos na sua agenda`, `somos líderes no mercado`, `atendemos grandes players`, `vi seu perfil e fiquei impressionado`, `posso roubar 2 minutos do seu dia`, `tudo bem? me chamo [X] da [Y]`.
3. **Pressão Falsa e Escassez Artificial:**
   - `últimas vagas`, `só hoje`, `promoção relâmpago`, `não perca essa chance`, `condição imperdível`, `última chamada`.
4. **Vícios de Formatação de IA:**
   - Travessão longo (`—`) no meio de mensagens de WhatsApp ou Direct.
   - Listas com vários emojis ou negrito excessivo em mensagem fria.
   - Textão com mais de 4 linhas em abertura de WhatsApp/Direct.

### Tabela de Substituição Obrigatória

| Banido (NUNCA USE) | Use no Lugar (Português Real) |
| :--- | :--- |
| *"alavancar suas vendas"* | *"trazer mais cliente pronto para fechar"* |
| *"transformação digital da empresa"* | *"organizar como o cliente encontra e fala com vocês"* |
| *"solução inovadora e escalável"* | *"estrutura simples que funciona no dia a dia"* |
| *"espero que este e-mail o encontre bem"* | *(Corte fora. Comece direto pelo fato observado.)* |
| *"apenas 15 minutinhos na sua agenda"* | *"posso te mandar em 3 linhas por aqui mesmo?"* |
| *"agregar valor ao seu negócio"* | *"evitar que cliente bom compare só preço e suma"* |
| *"vi seu perfil e fiquei impressionado"* | *"vi o perfil de vocês em [CIDADE] e notei um ponto específico..."* |

---

## ORDEM DIRETA 2: Lista Negra de Contatos (Bloqueio Definitivo)

Um contato entra **imediatamente e para sempre** na Lista Negra (`LISTA_NEGRA`) quando ocorrer qualquer um destes casos:
1. Pediu para sair (*"me tira da lista"*, *"para de mandar mensagem"*, *"não quero mais contato"*, *"descadastrar"*).
2. Disse um **"não" definitivo** (*"não tenho interesse"*, *"já temos quem faça e não vamos trocar"*).
3. Demonstrou irritação, ameaçou denúncia ou bloqueou o canal.
4. É **concorrente direto**, **cliente ativo** ou **contato bloqueado manualmente** pelo operador.

**Regras Rígidas do Bloqueio:**
- **Bloqueio cross-channel:** se o lead pediu para sair no WhatsApp, fica bloqueado também no LinkedIn, E-mail e Direct. Nunca tente contornar por outro número ou outra conta.
- **Checagem obrigatória pré-envio:** antes de cada disparo novo ou follow-up, valide telefone, e-mail, domínio e perfil contra a Lista Negra.

---

## ORDEM DIRETA 3: Parâmetros da Operação (Preencher Antes de Rodar)

Configure este bloco conforme o seu negócio antes de iniciar qualquer campanha:

```yaml
minha_oferta_principal: "[O que você vende + resultado prático em 1 frase]"
meu_plano_b: "[Opção de entrada menor / piloto pago]"
frase_de_valor_real: "[Quanto tempo, dinheiro ou risco isso devolve ao cliente]"
prova_real: "[1 resultado verdadeiro que você já entregou]"
ticket_medio: "[Faixa de valor]"
canais_ativos: ["WhatsApp", "LinkedIn", "Email", "Direct"]
nichos_alvo: "[Perfis com dor real e orçamento compatível]"
nichos_proibidos: "[Perfis que não fecham ou não têm margem]"
regiao_bloqueada: "[Cidades, estados ou praças onde você não prospecta]"
limites_diarios:
  whatsapp: 20
  linkedin_convites: 20
  email_por_caixa: 35
  direct: 15
janela_horario: "08:00-19:59"
```

---

## ORDEM DIRETA 4: Higiene de Fila, Bots e Saúde de Canal
- **Inválidos / Bounces:** telefone sem WhatsApp ou e-mail que deu bounce sai da fila imediatamente. Nunca reenvie em loop.
- **Filtro de Bots e Recepção:** saudação automática, menu numérico (*"Digite 1 para..."*) e aviso de ausência (*Out of Office*) **não são respostas humanas**. Não envie etapa de diagnóstico para robô.
- **Anti-rajada:** respeite intervalo mínimo entre buscas e envios para evitar erro 429, spam score alto ou bloqueio de linha/domínio.

---

## ORDEM DIRETA 5: Autópsia Pós-Perda e Treino Contínuo
Toda conversa importante encerrada ou lead perdido deve passar por uma revisão de 4 perguntas antes de seguir para o próximo lote:
1. **Canal e Etapa:** onde o lead travou (abertura, pesquisa, diagnóstico, exemplo, preço ou objeção)?
2. **Frase de Atrito:** qual frase exata sua gerou silêncio, resposta seca ou recusa?
3. **Falha de Qualificação:** esse lead deveria ter sido filtrado antes (sem decisor, nicho errado, sem orçamento)?
4. **Ajuste no Playbook:** qual mudança entra nas skills `01` a `05` para não repetir o mesmo erro na próxima conversa?
