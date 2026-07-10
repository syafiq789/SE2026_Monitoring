(() => {
  const sidebar = document.getElementById('sidebar');
  const toggle = document.getElementById('sidebarToggle');
  const backdrop = document.getElementById('sidebarBackdrop');
  if (!sidebar || !toggle || !backdrop) return;
  const close = () => { sidebar.classList.remove('open'); backdrop.classList.remove('show'); };
  toggle.addEventListener('click', () => { sidebar.classList.toggle('open'); backdrop.classList.toggle('show'); });
  backdrop.addEventListener('click', close);
  window.addEventListener('resize', () => { if (window.innerWidth >= 992) close(); });
})();

