document.addEventListener('DOMContentLoaded', async () => {
  try {
    const response = await fetch('/api/chart-data', {headers:{'Accept':'application/json'}});
    if (!response.ok) throw new Error('Data chart tidak tersedia');
    window.SE2026Charts.render(await response.json(), window.SE2026_SUMMARY);
  } catch (error) {
    document.querySelectorAll('.chart-wrap').forEach(node => node.innerHTML='<p class="text-muted text-center pt-5">Grafik tidak dapat dimuat.</p>');
  }
});

