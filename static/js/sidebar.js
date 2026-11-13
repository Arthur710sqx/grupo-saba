(() => {
  const menu=document.getElementById('sidebar-menu');
  if (!menu) return;
  const mobile=matchMedia('(max-width:900px)');
  function adapt(){menu.open=!mobile.matches;}
  adapt();
  mobile.addEventListener('change',adapt);
})();
