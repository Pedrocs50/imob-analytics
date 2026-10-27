/* Gráficos próprios das apresentações (HTML/SVG puro, texto nítido no projetor). Dados em dados.js. */
(() => {
  const D = window.DADOS || {};
  const v = (x, d = 2) => Number(x).toFixed(d).replace('.', ',');
  const ROT = {
    'condominio (R$)': 'Condomínio (R$)', 'no de comodidades': 'Nº de comodidades', 'suites': 'Suítes', 'banheiros': 'Banheiros',
    'vagas': 'Vagas', 'quartos': 'Quartos', 'area total': 'Área total', 'area util': 'Área útil'
  };
  const ITEM = {
    'seguranca': 'segurança', 'armarios planejados': 'armários planejados', 'area gourmet': 'área gourmet', 'salao de festas': 'salão de festas',
    'em condominio fechado': 'em condomínio fechado', '2+ suites': '2+ suítes', 'area acima da mediana': 'área acima da mediana'
  };
  const regra = (t) => t.split(' + ').map(i => ITEM[i] || i).join(' + ');
  const $ = (s, r = document) => r.querySelector(s);

  // 1) correlação de Spearman com intervalo de confiança (barras + whisker)
  window.graficoSpearman = (el, linhas) => {
    const MAX = 0.6;
    el.innerHTML = linhas.map(([nome, r, lo, hi], i) => {
      const pct = (x) => Math.max(0, x) / MAX * 100;
      return `<div class="barra-l ${i === 0 ? 'destaque' : ''}"><div class="rot">${ROT[nome] || nome}</div>
        <div class="trilho"><div class="pre" style="width:${pct(r)}%"></div><div class="ic" style="left:${pct(lo)}%;width:${pct(hi) - pct(lo)}%"></div></div>
        <div class="num">${v(r)}</div></div>`;
    }).join('');
  };

  // 2) tabela de regras de associação (com barra de confiança) ou validação em dados não vistos
  window.tabelaRegras = (el, tipo, dados) => {
    if (tipo === 'regras') {
      el.innerHTML = `<table class="tabela"><tr><th>Se o anúncio tem…</th><th style="text-align:right">Anúncios</th><th>Chance de ser "preço alto"</th><th style="text-align:right">Lift</th></tr>` +
        dados.slice(0, 7).map(([r, n, sup, conf, lift], i) => `<tr class="${i === 0 ? 'dest' : ''}"><td>${regra(r)}</td><td class="n">${n}</td>
        <td><span class="mini" style="width:${conf * 3.2}px"></span>${v(conf, 0)}%</td><td class="n">${v(lift, 1)}×</td></tr>`).join('') + `</table>`;
    } else {
      el.innerHTML = `<table class="tabela"><tr><th>Regra escolhida na metade A dos dados</th><th style="text-align:right">Lift na A</th><th>Lift na metade B (que a regra nunca viu)</th></tr>` +
        dados.slice(0, 7).map(([r, a, b]) => `<tr><td>${regra(r)}</td><td class="n">${v(a, 1)}×</td>
        <td><span class="mini v2" style="width:${b * 150}px"></span>${v(b, 1)}×</td></tr>`).join('') + `</table>`;
    }
  };

  // 3) tolerância x % dos anúncios (controle deslizante)
  window.graficoTolerancia = (raiz) => {
    const sl = $('input', raiz), alvoC = $('.t-casa', raiz), alvoA = $('.t-apto', raiz), tx = $('.t-tol', raiz);
    const busca = (arr, t) => (arr.find(x => x[0] === t) || [0, 0])[1];
    const pintar = () => {
      const t = +sl.value; tx.textContent = t;
      alvoC.textContent = v(busca(D.A.tol_casa, t), 0) + '%'; alvoA.textContent = v(busca(D.A.tol_apto, t), 0) + '%';
    };
    sl.oninput = pintar; pintar();
  };

  // 4) MAPE por horizonte (barras agrupadas SVG, legenda clicável)
  const CORES = { 'ARIMA': '#3b4a63', 'Tendência 12 meses': '#9aa5b1', 'Regressão linear': '#d4a017', 'LSTM sem macro': '#0a8f46',
    'LSTM com todo o macro': '#d90f1e', 'LSTM com macro escolhido': '#7a3db8' };
  window.graficoMape = (raiz, alvo) => {
    const dados = D.B.mape[alvo], nomes = Object.keys(dados), HS = [1, 3, 6, 12];
    raiz._off = raiz._off || new Set();
    const leg = $('.legenda-ch', raiz), svg = $('svg', raiz);
    leg.innerHTML = nomes.map(n => `<button class="${raiz._off.has(n) ? 'off' : ''}" data-n="${n}"><i style="background:${CORES[n]}"></i>${n}</button>`).join('');
    leg.querySelectorAll('button').forEach(b => b.onclick = () => { raiz._off.has(b.dataset.n) ? raiz._off.delete(b.dataset.n) : raiz._off.add(b.dataset.n); window.graficoMape(raiz, alvo); });
    const vis = nomes.filter(n => !raiz._off.has(n));
    const W = 1720, H = 560, mL = 90, mB = 60, mT = 20;
    const max = Math.max(...vis.flatMap(n => HS.map(h => dados[n][h])), 0.1) * 1.12;
    const gw = (W - mL) / HS.length, bw = Math.min(46, (gw * 0.82) / Math.max(vis.length, 1));
    let s = '';
    for (let i = 0; i <= 4; i++) { const y = mT + (H - mT - mB) * (1 - i / 4); s += `<line x1="${mL}" x2="${W}" y1="${y}" y2="${y}" stroke="#e3ece6" stroke-width="2"/><text x="${mL - 12}" y="${y + 8}" text-anchor="end" font-size="24" fill="#42554a">${v(max * i / 4, 1)}%</text>`; }
    HS.forEach((h, gi) => {
      const x0 = mL + gi * gw + (gw - bw * vis.length) / 2;
      vis.forEach((n, ni) => {
        const val = dados[n][h], hh = (H - mT - mB) * val / max, x = x0 + ni * bw, y = H - mB - hh;
        s += `<rect x="${x}" y="${y}" width="${bw - 4}" height="${hh}" rx="5" fill="${CORES[n]}"/>`;
        if (h === 12 || vis.length <= 4) s += `<text x="${x + (bw - 4) / 2}" y="${y - 8}" text-anchor="middle" font-size="22" font-weight="700" fill="#14221a">${v(val, 1)}</text>`;
      });
      s += `<text x="${mL + gi * gw + gw / 2}" y="${H - 18}" text-anchor="middle" font-size="28" font-weight="650" fill="#14221a">${h} ${h === 1 ? 'mês' : 'meses'} à frente</text>`;
    });
    svg.setAttribute('viewBox', `0 0 ${W} ${H}`); svg.innerHTML = s;
  };

  // 5) seleção x confirmação (RMSE relativo ao ARIMA; 1,0 = empate com o ARIMA)
  const SEL = {
    SJC: [['ARIMA', 1.00, 1.00], ['LSTM sem macro (pequena)', 0.84, 0.97], ['LSTM sem macro (base)', 0.84, 1.05],
      ['LSTM com macro escolhido', 0.83, 1.34, 1], ['LSTM com todo o macro', 1.08, 2.23], ['Regressão linear (só o alvo)', 1.01, 0.50]],
    nacional: [['ARIMA', 1.00, 1.00], ['LSTM sem macro (pequena)', 1.89, 1.18], ['LSTM sem macro (base)', 1.74, 1.01],
      ['LSTM com macro escolhido', 1.55, 1.81, 1], ['LSTM com todo o macro', 1.52, 2.75], ['Regressão linear (só o alvo)', 1.21, 1.08]]
  };
  window.graficoSelecao = (el, alvo) => {
    const MAX = 3, pos = (x) => Math.min(x, MAX) / MAX * 100;
    el.innerHTML = `<div style="display:flex;gap:30px;font-size:26px;margin-bottom:10px"><span><i style="display:inline-block;width:26px;height:26px;border-radius:6px;background:#f2b705;vertical-align:middle"></i> escolha (60% iniciais)</span>
      <span><i style="display:inline-block;width:26px;height:26px;border-radius:6px;background:#0a8f46;vertical-align:middle"></i> confirmação (40% finais)</span><span class="mut">linha vermelha = igual ao ARIMA (1,0) · menor é melhor</span></div>` +
      SEL[alvo].map(([n, a, b, dest]) => `<div style="display:grid;grid-template-columns:470px 1fr;align-items:center;gap:18px;margin:6px 0;${dest ? 'background:#fffbea;border-radius:12px;padding:6px 0' : ''}">
        <div style="text-align:right;font-size:28px;font-weight:${dest ? 800 : 600}">${n}</div>
        <div style="position:relative;height:74px">
          <div style="position:absolute;left:0;top:2px;height:32px;width:${pos(a)}%;background:#f2b705;border-radius:8px"></div>
          <span style="position:absolute;left:calc(${pos(a)}% + 10px);top:2px;font-size:26px;font-weight:700;line-height:32px">${v(a)}</span>
          <div style="position:absolute;left:0;top:38px;height:32px;width:${pos(b)}%;background:${b > 1.2 && dest ? '#d90f1e' : '#0a8f46'};border-radius:8px"></div>
          <span style="position:absolute;left:calc(${pos(b)}% + 10px);top:38px;font-size:26px;font-weight:800;line-height:32px">${v(b)}</span>
          <div style="position:absolute;left:${pos(1)}%;top:-6px;bottom:-6px;width:4px;background:#d90f1e;opacity:.75"></div></div></div>`).join('');
  };

  // liga os gráficos ao evento "render" dos slides (disparado ao entrar no slide e ao trocar de aba)
  document.querySelectorAll('[data-grafico]').forEach(raiz => {
    const slide = raiz.closest('.slide');
    slide.addEventListener('render', (e) => {
      const tab = e.detail, tipo = raiz.dataset.grafico;
      if (tipo === 'spearman') window.graficoSpearman(raiz, D.A['sp_' + tab]);
      if (tipo === 'regras') window.tabelaRegras(raiz, 'regras', D.A['regras_' + tab]);
      if (tipo === 'validacao') window.tabelaRegras(raiz, 'validacao', D.A['valid_' + tab]);
      if (tipo === 'mape') window.graficoMape(raiz, tab);
      if (tipo === 'selecao') window.graficoSelecao(raiz, tab);
    });
  });
  document.querySelectorAll('[data-tolerancia]').forEach(window.graficoTolerancia);
})();
