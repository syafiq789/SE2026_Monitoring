window.SE2026Charts = (() => {
  const brown='#6d3212', orange='#d96616', gold='#dba63a', cream='#ead9c7', green='#25835b', red='#bf3f32';
  Chart.defaults.font.family='Inter, Segoe UI, sans-serif'; Chart.defaults.color='#776b64';
  const baseOptions={responsive:true,maintainAspectRatio:false,plugins:{legend:{display:false}},scales:{y:{beginAtZero:true,max:100,grid:{color:'#eee5dc'},ticks:{callback:v=>`${v}%`}},x:{grid:{display:false},ticks:{maxRotation:45,minRotation:0}}}};
  const bar=(id,items,horizontal=false,color=orange)=>{const el=document.getElementById(id);if(!el)return;new Chart(el,{type:'bar',data:{labels:items.map(x=>x.label),datasets:[{data:items.map(x=>x.progress),backgroundColor:color,borderRadius:6,maxBarThickness:28}]},options:{...baseOptions,indexAxis:horizontal?'y':'x',scales:horizontal?{x:baseOptions.scales.y,y:{grid:{display:false}}}:baseOptions.scales}})};
  const render=(data,summary)=>{
    const upload=document.getElementById('uploadChart'); if(upload)new Chart(upload,{type:'doughnut',data:{labels:['Sudah Upload','Belum Upload'],datasets:[{data:[summary.total_processed,summary.total_remaining],backgroundColor:[green,cream],borderWidth:0}]},options:{responsive:true,maintainAspectRatio:false,cutout:'72%',plugins:{legend:{position:'bottom',labels:{usePointStyle:true,padding:18}}}}});
    bar('kecamatanChart',data.kecamatan); bar('pmlChart',data.pml); bar('pclChart',data.pcl); bar('lowKecChart',data.kecamatan_terendah,true,red); bar('lowPmlChart',data.pml_terendah,true,gold);
    const workflow=document.getElementById('workflowChart'); if(workflow)new Chart(workflow,{type:'bar',data:{labels:Object.keys(data.workflow),datasets:[{data:Object.values(data.workflow),backgroundColor:[brown,gold,green,orange,cream,red,'#9b6b52','#5c809b'],borderRadius:5}]},options:{responsive:true,maintainAspectRatio:false,plugins:{legend:{display:false}},scales:{y:{beginAtZero:true,grid:{color:'#eee5dc'}},x:{grid:{display:false},ticks:{maxRotation:45,minRotation:25}}}}});
  }; return {render};
})();

