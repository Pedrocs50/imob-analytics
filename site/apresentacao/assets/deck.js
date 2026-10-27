/* Motor da apresentação: navegação, passos, abas, notas do apresentador, visão geral. Sem dependências. */
(() => {
  const stage = document.querySelector('.stage');
  const slides = [...document.querySelectorAll('.slide')];
  const barra = document.querySelector('.rodape .prog i');
  const contador = document.querySelector('.rodape .cont');
  const secao = document.querySelector('.topo .secao');
  const lightbox = document.querySelector('.lightbox');
  const visao = document.querySelector('.overlay.visao');
  const aviso = document.querySelector('.nota-rapida');
  let atual = 0, janelaNotas = null, inicio = null;

  const ajustar = () => {
    const s = Math.min(innerWidth / 1920, innerHeight / 1080);
    stage.style.transform = `translate(-50%,-50%) scale(${s})`;
  };
  addEventListener('resize', ajustar); ajustar();

  const frags = (s) => [...s.querySelectorAll('[data-frag]')].sort((a, b) => (+a.dataset.frag) - (+b.dataset.frag));
  const aviso_ = (txt) => { aviso.textContent = txt; aviso.classList.add('on'); clearTimeout(aviso._t); aviso._t = setTimeout(() => aviso.classList.remove('on'), 1400); };

  function abas(s) {
    const botoes = [...s.querySelectorAll('.seg button[data-v]')];
    if (!botoes.length) return;
    const pintar = () => {
      const v = s.dataset.tab;
      botoes.forEach(b => b.classList.toggle('on', b.dataset.v === v));
      s.querySelectorAll('[data-tab]').forEach(e => e.classList.toggle('show', e.dataset.tab.split(' ').includes(v)));
      s.dispatchEvent(new CustomEvent('render', { detail: v }));
    };
    if (!s.dataset.tab) s.dataset.tab = botoes[0].dataset.v;
    botoes.forEach(b => b.onclick = () => { s.dataset.tab = b.dataset.v; pintar(); });
    s._pintar = pintar; pintar();
  }
  slides.forEach(abas);

  function ir(n, fim) {
    n = Math.max(0, Math.min(slides.length - 1, n));
    slides.forEach((s, i) => s.classList.toggle('on', i === n));
    atual = n;
    const s = slides[n];
    frags(s).forEach(f => f.classList.toggle('vis', !!fim));
    stage.classList.toggle('capa', s.classList.contains('capa-slide'));
    barra.style.width = ((n + 1) / slides.length * 100) + '%';
    contador.textContent = `${n + 1} / ${slides.length}`;
    if (secao && s.dataset.secao) secao.innerHTML = s.dataset.secao;
    history.replaceState(null, '', '#' + (n + 1));
    s.dispatchEvent(new CustomEvent('render', { detail: s.dataset.tab }));
    atualizarNotas();
  }
  const proximo = () => {
    const s = slides[atual], f = frags(s).find(x => !x.classList.contains('vis'));
    if (f) f.classList.add('vis'); else if (atual < slides.length - 1) ir(atual + 1, false);
  };
  const anterior = () => {
    const s = slides[atual], vis = frags(s).filter(x => x.classList.contains('vis'));
    if (vis.length) vis[vis.length - 1].classList.remove('vis'); else if (atual > 0) ir(atual - 1, true);
  };

  // notas do apresentador (janela separada, com cronômetro)
  const notasDe = (s) => (s.querySelector('aside.notas') || {}).innerHTML || '<p>(sem notas)</p>';
  const tituloDe = (s) => (s.dataset.titulo || (s.querySelector('.titulo') || {}).textContent || 'Capa').trim();
  function atualizarNotas() {
    if (!janelaNotas || janelaNotas.closed) return;
    const d = janelaNotas.document, s = slides[atual], prox = slides[atual + 1];
    d.getElementById('n').innerHTML = notasDe(s);
    d.getElementById('t').textContent = `${atual + 1}/${slides.length} · ${tituloDe(s)}`;
    d.getElementById('p').textContent = prox ? 'Próximo: ' + tituloDe(prox) : 'Fim';
    d.getElementById('m').textContent = s.dataset.min ? `Tempo sugerido: ~${s.dataset.min} min` : '';
  }
  function abrirNotas() {
    janelaNotas = open('', 'notas', 'width=720,height=760');
    if (!janelaNotas) { aviso_('O navegador bloqueou a janela de notas'); return; }
    janelaNotas.document.write(`<!doctype html><meta charset="utf-8"><title>Notas</title>
      <style>body{font:22px/1.45 system-ui,sans-serif;margin:0;padding:20px;background:#fafaf7;color:#14221a}
      #t{font-weight:700;color:#06602f;font-size:24px}#p,#m{color:#555;font-size:18px}#r{float:right;font:700 40px monospace}
      li,p{font-size:22px;margin:8px 0}hr{border:0;border-top:1px solid #ccc}</style>
      <div id="r">00:00</div><div id="t"></div><div id="p"></div><div id="m"></div><hr><div id="n"></div>`);
    if (!inicio) inicio = Date.now();
    const tick = () => { if (janelaNotas.closed) return; const sec = Math.floor((Date.now() - inicio) / 1000);
      janelaNotas.document.getElementById('r').textContent = String(Math.floor(sec / 60)).padStart(2, '0') + ':' + String(sec % 60).padStart(2, '0'); setTimeout(tick, 500); };
    tick(); atualizarNotas();
  }

  function montarVisao() {
    visao.querySelector('ol').innerHTML = slides.map((s, i) => `<li data-i="${i}">${tituloDe(s)}</li>`).join('');
    visao.querySelectorAll('li').forEach(li => li.onclick = () => { visao.classList.remove('on'); ir(+li.dataset.i); });
  }
  montarVisao();

  addEventListener('keydown', (e) => {
    if (e.target.matches('input,textarea,select')) return;
    const k = e.key;
    if (lightbox.classList.contains('on')) { lightbox.classList.remove('on'); return; }
    if (['ArrowRight', 'PageDown', ' ', 'Enter'].includes(k)) { e.preventDefault(); proximo(); }
    else if (['ArrowLeft', 'PageUp', 'Backspace'].includes(k)) { e.preventDefault(); anterior(); }
    else if (k === 'Home') ir(0); else if (k === 'End') ir(slides.length - 1);
    else if (k === 'f' || k === 'F') { document.fullscreenElement ? document.exitFullscreen() : document.documentElement.requestFullscreen().catch(() => {}); }
    else if (k === 'g' || k === 'G' || k === 'Escape') visao.classList.toggle('on', (k !== 'Escape') && !visao.classList.contains('on'));
    else if (k === 'p' || k === 'P') abrirNotas();
    else if (k === 'Tab') {
      e.preventDefault(); const s = slides[atual], bs = [...s.querySelectorAll('.seg button[data-v]')];
      if (bs.length) { const i = bs.findIndex(b => b.dataset.v === s.dataset.tab); bs[(i + 1) % bs.length].click(); aviso_('Aba: ' + bs[(i + 1) % bs.length].textContent); }
    }
  });
  // clique: avança (exceto em controles); clique em figura amplia
  stage.addEventListener('click', (e) => {
    if (e.target.closest('button,input,a,iframe,table,.seg,.overlay,.nao-avanca')) return;
    const img = e.target.closest('.fig img');
    if (img) { lightbox.querySelector('img').src = img.src; lightbox.classList.add('on'); return; }
    proximo();
  });
  lightbox.addEventListener('click', () => lightbox.classList.remove('on'));
  let x0 = null;
  stage.addEventListener('touchstart', (e) => { x0 = e.touches[0].clientX; }, { passive: true });
  stage.addEventListener('touchend', (e) => { if (x0 === null) return; const dx = e.changedTouches[0].clientX - x0; if (Math.abs(dx) > 60) (dx < 0 ? proximo : anterior)(); x0 = null; });

  window.DECK = { ir, proximo, anterior, slides };
  const h = parseInt(location.hash.slice(1), 10);
  ir(Number.isFinite(h) ? h - 1 : 0, false);
})();
