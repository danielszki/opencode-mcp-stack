// Números de cada público e aparelho. Usado por medidas.mjs e chicotada.mjs.
export const PERFIS = {
  geral: { corpo: 17, minimo: 13, razao: 1.25, entrelinha: 1.5, alvo: 44, contraste: 4.5, opcoes: 5, movimento: "médio", porque: "público amplo: 17px lê bem sem zoom e 1,25 dá hierarquia clara sem saltos bruscos" },
  idoso: { corpo: 19, minimo: 15, razao: 1.2, entrelinha: 1.6, alvo: 52, contraste: 7, opcoes: 3, movimento: "mínimo", porque: "acuidade e contraste percebido caem com a idade; tremor pede alvo maior; menos opções por tela (Hick)" },
  jovem: { corpo: 16, minimo: 12, razao: 1.333, entrelinha: 1.5, alvo: 44, contraste: 4.5, opcoes: 5, movimento: "rico", porque: "leitura rápida no celular; contraste de tamanho maior (1,333) dá o drama que esse público espera" },
  b2b: { corpo: 16, minimo: 13, razao: 1.25, entrelinha: 1.5, alvo: 44, contraste: 4.5, opcoes: 7, movimento: "discreto", porque: "decisor lê comparando; densidade média e números alinhados importam mais que impacto" },
  tecnico: { corpo: 15, minimo: 12, razao: 1.2, entrelinha: 1.45, alvo: 40, contraste: 4.5, opcoes: 9, movimento: "discreto", porque: "uso em desktop com mouse, tela densa; saltos pequenos para caber mais informação legível" },
};
export const APARELHOS = {
  fraco: { pesoKB: 700, jsKB: 120, tresD: "proibido (use imagem estática)", video: "proibido", porque: "Android de entrada e 4G ruim: cada 100 KB a mais custa ~0,5 s" },
  medio: { pesoKB: 1200, jsKB: 250, tresD: "só sob demanda, com imagem de reserva", video: "proibido no celular", porque: "intermediário: aguenta pouco JS e imagens bem comprimidas" },
  forte: { pesoKB: 2000, jsKB: 450, tresD: "permitido, com reserva", video: "só com poster e sem som", porque: "aparelho recente, mas o site ainda precisa abrir rápido para quem não tem" },
};

