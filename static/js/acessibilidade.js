(() => {
  'use strict';
  const panel = document.getElementById('access-panel');
  const launcher = document.getElementById('abrir-acesso');
  const guide = document.getElementById('reading-guide');
  const options = {'alto-contraste':'high-contrast','inverter':'inverted','cinza':'grayscale','letras':'spaced-letters','linhas':'spaced-lines','links':'highlight-links','titulos':'highlight-titles','regua':'ruler','mascara':'mask','menos-movimento':'reduce-motion'};
  let preferences = {};
  try {
    const saved = JSON.parse(localStorage.getItem('saba-accessibility') || '{}');
    if (saved && typeof saved === 'object' && !Array.isArray(saved)) preferences = saved;
  } catch (_) {}
  let font = Number(preferences.font);
  preferences.font = Number.isFinite(font) ? Math.max(80, Math.min(200, font)) : preferences['texto-maior'] ? 125 : 100;
  let position = 50;
  function move(value) {
    position = Math.max(5, Math.min(95, value));
    guide.style.top = position + 'vh';
    document.getElementById('reading-position').value = position;
  }
  function apply() {
    document.documentElement.classList.remove('large-text');
    document.documentElement.style.fontSize = preferences.font + '%';
    document.getElementById('font-value').textContent = preferences.font + '%';
    document.getElementById('fonte-menos').disabled = preferences.font <= 80;
    document.getElementById('fonte-mais').disabled = preferences.font >= 200;
    Object.entries(options).forEach(([id, css]) => {
      const enabled = preferences[id] === true;
      document.documentElement.classList.toggle(css, enabled);
      document.getElementById(id).setAttribute('aria-pressed', String(enabled));
    });
    guide.hidden = !(preferences.regua || preferences.mascara);
    guide.classList.toggle('mask', preferences.mascara === true);
    guide.classList.toggle('ruler', preferences.regua === true);
  }
  function save() {
    apply();
    try { localStorage.setItem('saba-accessibility', JSON.stringify(preferences)); } catch (_) {}
    document.getElementById('access-status').textContent = 'Preferências aplicadas.';
  }
  launcher.addEventListener('click', () => { panel.showModal(); document.getElementById('fechar-acesso').focus(); });
  document.getElementById('fechar-acesso').addEventListener('click', () => panel.close());
  panel.addEventListener('close', () => launcher.focus());
  Object.keys(options).forEach(id => document.getElementById(id).addEventListener('click', () => { preferences[id] = preferences[id] !== true; save(); }));
  document.getElementById('fonte-mais').addEventListener('click', () => { preferences.font = Math.min(200, preferences.font + 10); save(); });
  document.getElementById('fonte-menos').addEventListener('click', () => { preferences.font = Math.max(80, preferences.font - 10); save(); });
  document.getElementById('restaurar-acesso').addEventListener('click', () => { preferences = {font:100}; move(50); save(); });
  document.getElementById('reading-position').addEventListener('input', e => move(Number(e.target.value)));
  document.addEventListener('pointermove', e => { if (!guide.hidden && !panel.open) move(e.clientY / innerHeight * 100); });
  document.addEventListener('pointerdown', e => { if (!guide.hidden && !panel.open) move(e.clientY / innerHeight * 100); });
  document.addEventListener('focusin', e => {
    if (!guide.hidden && !panel.open && e.target !== launcher) {
      const rect=e.target.getBoundingClientRect(); move((rect.top+rect.height/2)/innerHeight*100);
    }
  });
  document.addEventListener('keydown', e => {
    if (!guide.hidden && !panel.open && !e.target.closest('input,textarea,select,button,a,[contenteditable]') && ['ArrowUp','ArrowDown'].includes(e.key)) {
      e.preventDefault(); move(position + (e.key === 'ArrowUp' ? -5 : 5));
    }
  });
  document.querySelectorAll('a[target="_blank"]').forEach(link => {
    const hint = document.createElement('span'); hint.className='sr-only'; hint.textContent=' (abre em nova aba)'; link.append(hint);
  });
  document.querySelectorAll('input[required],select[required],textarea[required]').forEach(field => {
    const label=field.closest('label');
    if(label){const hint=document.createElement('span');hint.textContent=' (obrigatório)';label.append(hint);}
  });
  const error=document.querySelector('.flash.erro'); if(error)error.focus();
  const heading=document.querySelector('main h1'); if(heading)document.title=heading.textContent+' | Grupo Sabá';
  apply();
})();
