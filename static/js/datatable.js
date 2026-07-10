document.addEventListener('DOMContentLoaded', () => {
  if (!window.jQuery || !jQuery.fn.DataTable) return;
  document.querySelectorAll('.data-table').forEach(table => {
    if (jQuery.fn.DataTable.isDataTable(table)) return;
    jQuery(table).DataTable({
      responsive: false,
      scrollX: true,
      pageLength: 25,
      lengthMenu: [[10,25,50,100,-1],[10,25,50,100,'Semua']],
      order: [],
      language: {
        search: 'Cari:', lengthMenu: 'Tampilkan _MENU_ data', info: 'Menampilkan _START_–_END_ dari _TOTAL_ data',
        infoEmpty: 'Tidak ada data', zeroRecords: 'Data tidak ditemukan', emptyTable: 'Belum ada data yang tersedia',
        paginate: { first: 'Pertama', last: 'Terakhir', next: 'Berikutnya', previous: 'Sebelumnya' }
      }
    });
  });
});

