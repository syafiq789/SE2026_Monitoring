(() => {
  const kec = document.getElementById('kecFilter');
  const desa = document.getElementById('desaFilter');
  const pml = document.getElementById('pmlFilter');
  const pcl = document.getElementById('pclFilter');
  if (!kec || !desa || !pml || !pcl) return;
  const fill = (select, items, placeholder, key='id') => {
    const value = select.value;
    select.innerHTML = `<option value="">${placeholder}</option>` + items.map(item => `<option value="${item[key]}">${item.code ? `${item.code} · ` : ''}${item.name}</option>`).join('');
    if ([...select.options].some(option => option.value === value)) select.value = value;
  };
  const refresh = async (keepPml=false) => {
    const params = new URLSearchParams();
    if (kec.value) params.set('kec_code', kec.value);
    if (keepPml && pml.value) params.set('pml_id', pml.value);
    try {
      const response = await fetch(`/api/filter-data?${params}`, {headers:{'Accept':'application/json'}});
      if (!response.ok) return;
      const data = await response.json();
      if (!keepPml) { fill(desa, data.desa, 'Semua Desa', 'code'); fill(pml, data.pml, 'Semua PML'); }
      fill(pcl, data.pcl, 'Semua PCL');
    } catch (_) { /* Form server-side tetap berfungsi tanpa AJAX. */ }
  };
  kec.addEventListener('change', () => refresh(false));
  pml.addEventListener('change', () => refresh(true));
})();

