# 7. Imagem, 3D e nichos regulados

## Quantas imagens

Imagem é prova ou atmosfera. Se não é nenhuma das duas, é peso.

| Situação | Densidade |
|---|---|
| Negócio de serviço local (barbearia, clínica, restaurante) | alta: foto real do lugar, da equipe, do resultado permitido |
| SaaS / ferramenta | a tela real do produto vale mais que qualquer foto |
| Profissional liberal (advogado, contador, engenheiro) | retrato real + o lugar + um detalhe do trabalho (mínimo de 3 peças, como toda página), com tipografia forte |
| Aparelho `fraco` | as mesmas 3 peças visuais no mínimo, mas comprimidas (640px), só 1 acima da dobra e o resto com `loading="lazy"`. Aparelho fraco muda o peso da foto, nunca tira a foto |

Ordem de preferência: **foto real do cliente > tela real do produto > foto gerada com prompt bem feito > banco de imagem**. Banco de imagem com pessoa nunca entra como se fosse o profissional ou o cliente.

## Banco de imagem: Pexels

```bash
node scripts/pexels.mjs --busca "barber shop interior warm light" --quantos 6 --orientacao landscape --saida public/img
node scripts/pexels.mjs --ids 6372911,8532753 --saida public/img     # quando já sabe as fotos
```

- Não precisa de chave: a busca abre o pexels.com no mesmo Chromium da chicotada e o download vem direto de `images.pexels.com`. Com `PEXELS_API_KEY` no ambiente, usa a API oficial (traz o nome do fotógrafo).
- Já baixa em duas larguras (800 e 1600) para o `srcset`.
- Busque em inglês, com luz e ambiente na busca ("warm light", "top view", "minimal").
- O script grava `CREDITOS.md`. Ponha "Imagens ilustrativas: Pexels" no rodapé quando usar.
- Converta para AVIF/WebP antes de publicar, se a stack não fizer isso sozinha.
- **Sem foto boa?** Antes de cair no banco de imagem genérico, veja se um efeito desenhado com código diz mais (`15-efeitos.md`).

## Prompt para gerar a imagem (ChatGPT, Gemini, Midjourney)

Quando a imagem certa não existe, entregue o prompt pronto, um por vaga, neste formato:

```
Vaga: hero, lado direito, 5/12 colunas, sangrando para a borda
Proporção: 4:5 (celular) e 16:10 (desktop)
Prompt: [assunto concreto], [ação], [ambiente], [luz: direção e cor], [lente/enquadramento],
espaço vazio à esquerda para o texto, paleta [cores da página], sem texto na imagem, sem marca d'água,
fotografia realista, sem pessoas de frente para a câmera [se nicho regulado]
Por quê: [o que a imagem prova ou que sensação ela cria nesta dobra]
```

Diga onde ela entra e o que fazer se a pessoa não gerar (reserva: cor sólida da paleta, padrão em CSS ou a forma da metáfora).

## 3D

Pergunte: **o 3D mostra algo que a foto não mostra?** (o produto girando, um imóvel por dentro, uma peça técnica). Se não, não use.

Quando usar:
- Só em aparelho `medio` ou `forte`, carregado depois da primeira tela (`IntersectionObserver` ou clique em "ver em 3D").
- Sempre com imagem estática de reserva (`<img>` com o mesmo enquadramento), que é o que entra no LCP.
- Pause quando sair da tela e com `prefers-reduced-motion: reduce`.
- Orçamento: modelo comprimido (glTF + Draco/Meshopt) ≤ 1,5 MB, carregado sob demanda.

## Nichos regulados (Brasil)

Lição da Korely (resumo, não parecer jurídico; confirme com o conselho antes de publicar):

| Nicho | Regra prática |
|---|---|
| Medicina (CFM 2.336/2023) | sem promessa de resultado; sem antes e depois; especialidade só com RQE; depoimento sóbrio |
| Odontologia, fisioterapia, psicologia (CRO, CREFITO, CRP) | aplique o mesmo cuidado do CFM e confira a norma própria |
| Advocacia (Provimento 205/2021 OAB) | sem preço, sem promessa de resultado, sem linguagem de captação; contato só iniciado pelo visitante; avaliações discretas e no fim |
| Nutrição (CFN) | sem antes e depois, sem imagem de corpo, sem depoimento de peso perdido |

Em todos: nada de inventar formação, registro, prêmio ou número. Campo sem dado some da página.
