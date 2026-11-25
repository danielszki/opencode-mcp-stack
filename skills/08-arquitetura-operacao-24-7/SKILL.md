---
name: 08-arquitetura-operacao-24-7
description: Blueprint completo de arquitetura para rodar prospecção e vendas 24/7 sem vazar base nem derrubar número: estrutura de banco/CRM, endpoints de API, workers em rotina (monitoramento, disparo cadenciado e busca), aquecimento de chip em grupos de WhatsApp, limites anti-banimento e logs de conversão. Use ao montar ou escalar a infraestrutura técnica da operação.
---

# 08. Arquitetura de Operação 24/7 (API, CRM e Blindagem de Número)

Skill sem estrutura técnica vira trabalho manual. Esta skill mostra **como montar a máquina** para rodar 24/7 com segurança, previsibilidade e taxa de bloqueio próxima de zero.

## Ordens Diretas ao Agente
1. **Nunca dispare em rajada:** respeite rigorosamente teto diário, teto por hora, janela de horário e intervalo aleatório entre mensagens.
2. **Use sempre UTF-8 nativo ponta a ponta:** ao integrar scripts com APIs de mensageria, nunca use ferramentas que corrompem acentos em português; prefira Python ou Node com encoding `utf-8` explícito.
3. **Cheque a lista negra na API antes de todo envio:** nenhum worker pode disparar sem validar se o contato já deu opt-out ou é inválido.
4. **Ignore bots na automação:** o worker de monitoramento só deve acordar o fluxo de negociação quando detectar resposta humana real após o último envio.

---

## 1. Estrutura Mínima de CRM / Banco de Dados

Você não precisa de CRM caro para começar. Um banco relacional simples (Postgres/SQLite) com 4 tabelas resolve 100% da operação:

| Tabela | Campos Essenciais | Função na Máquina |
| :--- | :--- | :--- |
| **`leads`** | `id`, `nome`, `telefone`, `email`, `cidade`, `nicho`, `site`, `etapa`, `sem_whatsapp`, `criado_em`, `contatado_em` | Guarda a fila única e o estado atual de cada contato |
| **`mensagens`** | `id`, `lead_id`, `direcao` (`nos` / `lead`), `texto`, `automatica` (`bool`), `em` | Histórico completo para o agente ler contexto antes de responder |
| **`lista_negra`** | `id`, `telefone`, `email`, `motivo`, `criado_em` | Bloqueio definitivo cross-channel; consultada antes de todo envio |
| **`execucoes_log`** | `ts`, `lead_id`, `acao`, `status_http`, `erro` | Auditoria em JSONL para medir taxa de resposta por nicho/abertura |

### Máquina de Estados (Etapas do Funil)
`ENCONTRADO` -> `CONTATO_FEITO` -> `RESPONDEU` -> `DIAGNOSTICO` -> `PROPOSTA` -> `FECHADO_GANHO` | `PERDIDO` | `LISTA_NEGRA`

---

## 2. Arquitetura de API Desacoplada (5 Endpoints Essenciais)

Separe o cérebro (agente de IA + skills) do transporte (WhatsApp / E-mail / LinkedIn) usando uma API REST simples:

1. **`POST /leads/buscar`** -> Busca novos contatos públicos por nicho/cidade, filtra quem já existe no banco e salva em `ENCONTRADO` (priorizando quem tem lacuna clara, ex: sem site).
2. **`GET /leads?etapa=ENCONTRADO`** -> Entrega a fila pronta para o worker de disparo.
3. **`GET /leads/{id}/conversa`** -> Retorna todas as mensagens do lead para o agente decidir o próximo passo com contexto real.
4. **`POST /mensagens/enviar`** -> Valida lista negra, verifica se o número tem WhatsApp ativo, envia pela sessão conectada e grava na tabela `mensagens`.
5. **`GET /lista-negra/checar`** -> Trava de segurança antes de qualquer abordagem ou follow-up.

---

## 3. Os 3 Workers para Rodar 24/7 (Sem Travar Contexto)

| Worker | Frequência | O Que Faz na Prática |
| :--- | :--- | :--- |
| **1. Monitor de Respostas** | A cada **10 min** | Varre leads em `CONTATO_FEITO` e `RESPONDEU`. Se a última mensagem for do lead (`automatica = false`), aciona o agente para responder usando as skills `03`, `04` e `07`. Se não houver nada novo, encerra em silêncio. |
| **2. Disparo Cadenciado** | A cada **1 hora** (dentro de `08:00-19:59`) | Checa quantos envios novos já saíram hoje e nesta hora. Se estiver abaixo do teto, pega 1 a 2 leads Tier A da fila `ENCONTRADO`, valida lista negra e envia a abertura (Skill `01`). |
| **3. Abastecedor de Fila** | Sob demanda (quando fila < 10) | Busca 1 praça/nicho por vez com pausa de 10 a 15 segundos entre requisições para evitar erro `429` (rate limit). |

---

## 4. Blindagem de Número no WhatsApp (O Que Fazer Para Não Cair)

Chip novo disparando mensagem fria cai em poucas horas. Siga este protocolo à risca:

### Fase A: Aquecimento de Chip (14 a 21 Dias Antes de Escalar)
- **Dias 1 a 4 (Vida Real):** use o número como pessoa normal. Converse com 5 a 10 contatos conhecidos (texto, áudio curto, foto). **Entre em 3 a 5 grupos ativos de WhatsApp** (comunidades do seu nicho, associações, grupos de networking local) para gerar volume natural de mensagens recebidas e lidas.
- **Dias 5 a 10 (Entrada Leve):** comece com **2 a 5 abordagens novas por dia**, espaçadas ao longo do dia. Priorize mensagens que geram resposta curta (*"Posso te mandar rapidinho?"*).
- **Dias 11 a 21 (Ritmo de Cruzeiro):** suba gradualmente para **10 a 20 novos contatos por dia**, no máximo **1 a 3 disparos por hora**, sempre dentro do horário comercial (`08:00-19:59`).

### Fase B: As 6 Regras Anti-Banimento
1. **Proporção Recebida vs. Enviada:** número que só manda mensagem e quase ninguém responde acende alerta vermelho. A 1ª mensagem **precisa** ser leve e pedir uma resposta simples para equilibrar a proporção.
2. **Zero link e zero anexo no primeiro contato:** mandar URL fria para quem não tem seu número salvo é o gatilho número 1 de bloqueio e denúncia.
3. **Espaçamento e Jitter:** nunca dispare em lote no mesmo minuto. Coloque atraso aleatório (ex: 15 a 45 minutos entre contatos novos).
4. **Variação de texto:** nunca mande a mesma string idêntica 50 vezes. Varie pequenas palavras mantendo a mesma estrutura.
5. **Tratamento de `sem_whatsapp`:** se o gateway retornar que o número não tem WhatsApp (`422`), marque `sem_whatsapp = true` e pule imediatamente. Tentar enviar repetidamente para números inválidos derruba a conta.
6. **Zero insistência após "não":** quem é bloqueado ou denunciado 3 vezes no mesmo dia perde o chip. Pediu para sair, entra na Lista Negra na hora.

---

## 5. Uso Inteligente de Grupos de WhatsApp (Aquecimento + Venda)
Entrar em grupos do seu público-alvo serve para duas coisas ao mesmo tempo:
1. **Saúde do número:** grupos ativos geram fluxo constante de mensagens recebidas e interações legítimas.
2. **Captação de demanda quente:** observe quem pede indicação, reclama de fornecedor ou tira dúvida ligada ao que você resolve.
   - **Regra de ouro:** nunca faça spam ou pitch aberto dentro do grupo. Chame a pessoa no privado citando o contexto real: *"Oi [NOME], vi sua dúvida lá no grupo [NOME_DO_GRUPO] sobre [TEMA]. Posso te mandar uma sugestão rápida que costuma resolver isso?"*

---

## 6. Logs e Otimização Contínua (Dados > Achismo)
Salve cada tentativa em um arquivo `logs/envios.jsonl` com timestamp, cidade, nicho, modelo de abertura e resultado:
- **Taxa de resposta < 10%:** o problema está na **abertura** (parece robô, tem jargão ou tem oferta cedo demais) ou na **qualidade da lista** (contatos sem a dor).
- **Respondem mas somem depois do preço:** o problema está no **diagnóstico** (Skill `03`: faltou dor, faltou Regra do Imaginar ou falou preço antes da hora).
- **Muitos erros `422 sem_whatsapp`:** mude a fonte de extração ou o filtro de busca (números fixos antigos têm baixa taxa de WhatsApp ativo).
