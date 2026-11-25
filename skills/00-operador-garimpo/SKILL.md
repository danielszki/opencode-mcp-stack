---
name: 00-operador-garimpo
description: Como operar a prospecção pelo sistema Garimpo via API (/api/v1). Leia primeiro, antes das skills 01 a 08. Diz a rotina do dia, a ordem das chamadas e o que nunca fazer.
---

# 00. Operador do Garimpo

Você opera a prospecção de ponta a ponta pelo sistema. As skills 01 a 08 dizem **o que** falar; esta diz **por onde** fazer.

## Antes de qualquer coisa
1. `GET /api/v1` — o mapa da API (rotas, corpos de exemplo, regras).
2. `GET /api/v1/skills?conteudo=1` — todas as skills ativas. Siga a `06-lista-negra-e-governanca` como lei.
3. `GET /api/v1/lista-negra` — termos proibidos e regras de escrita. Nada disso pode sair num texto seu.
4. `GET /api/v1/conversas/travas` — se `pausado: true`, você não envia nada hoje; só prepara.

Toda chamada leva `Authorization: Bearer <SUA_CHAVE>`. Dinheiro sempre em centavos.

## Rotina do dia (nesta ordem)
1. **Responder quem respondeu.** `GET /api/v1/conversas/novas?desde=<última vez>`. Para cada resposta: leia a ficha (`GET /api/v1/negocios/{id}`), escreva seguindo as skills 03 e 04, confira em `POST /api/v1/lista-negra/checar` e envie em `POST /api/v1/conversas/enviar`.
2. **Achar negócios novos.** `POST /api/v1/rastro` com `{ "tipo": "...", "cidade": "...", "limite": 5, "adicionar": true }`. Ele já pula quem está na esteira. Prefira quem tem nota alta e **não tem site**.
3. **Pesquisar antes de abordar** (skill 02). Anote o que achou: `POST /api/v1/negocios/{id}/notas`.
4. **Gerar a prévia.** `GET /api/v1/modelos` → escolha o modelo que combina com o nicho → `POST /api/v1/previas { negocioId, modeloId, valores }`. Use o `link` devolvido.
5. **Primeira mensagem** (skill 01): curta, sem pitch, sem preço. Envie por `POST /api/v1/conversas/enviar`. Respeite o 409: o sistema espaça as primeiras mensagens sozinho.
6. **Fechou?** `POST /api/v1/cobrancas { titulo, valor, negocioId, email }` e mande o `link`. Quando pagar, o negócio vai para Fechado sozinho.
7. **Não quis?** `POST /api/v1/negocios/{id}/etapa { "etapa": "DESCARTADO", "motivo": "sem_interesse" }`.

## Erros do envio (409) e o que fazer
| erro | o que fazer |
| --- | --- |
| `pausado` | Pare. Só prepare rascunhos e notas. |
| `modo_teste` | O dono ainda está testando. Não tente outro número. |
| `limite_diario` | Pare de enviar até amanhã. |
| `espacamento` | Espere até `liberaEm` para a próxima primeira mensagem. Pode responder conversas em andamento. |
| `lista_negra` | Reescreva sem os termos de `violacoes` e confira de novo. Nunca contorne. |
| `conversa_parada` | A pessoa pediu para parar ou pediu um humano. Não envie nada. |
| `sem_whatsapp` | Descarte com motivo `sem_whatsapp` ou ache outro contato. |
| `desconectado` | O WhatsApp caiu. Avise o dono com uma nota e pare. |

## Nunca
- Nunca envie mensagem por fora do `/conversas/enviar`.
- Nunca invente dado do negócio: se não sabe, pergunte ou deixe de fora.
- Nunca mande preço ou link de pagamento na primeira mensagem.
- Nunca insista depois de um "não".

## Melhorando o sistema
- Achou um vício de texto? `POST /api/v1/lista-negra`.
- Aprendeu uma abordagem que funciona num nicho? `POST /api/v1/skills` com uma skill nova (ex.: `abordagem-clinicas`).
- Tem um HTML de página melhor? `POST /api/v1/modelos` com `{{nome}}`, `{{cidade}}`… no lugar dos textos.
