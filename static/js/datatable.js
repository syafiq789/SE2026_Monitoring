/**
 * Inisialisasi DataTables untuk tabel monitoring SE2026.
 * Mendukung tema Bootstrap 5, pencarian cepat, sorting, dan translasi Bahasa Indonesia.
 */
document.addEventListener('DOMContentLoaded', () => {
  if (!window.jQuery || !jQuery.fn.DataTable) return;

  // Inisialisasi otomatis untuk semua tabel bertipe .data-table kecuali #slsTable (yang memakai Server-Side AJAX)
  document.querySelectorAll('.data-table').forEach(table => {
    if (table.id === 'slsTable') return;
    if (jQuery.fn.DataTable.isDataTable(table)) return;

    jQuery(table).DataTable({
      responsive: false,
      scrollX: true,
      pageLength: 25,
      lengthMenu: [
        [10, 25, 50, 100, -1],
        [10, 25, 50, 100, 'Semua']
      ],
      order: [],
      language: {
        search: 'Cari:',
        searchPlaceholder: 'Ketik untuk memfilter...',
        lengthMenu: 'Tampilkan _MENU_ data',
        info: 'Menampilkan _START_ s/d _END_ dari total _TOTAL_ data',
        infoEmpty: 'Menampilkan 0 data',
        infoFiltered: '(disaring dari _MAX_ total data)',
        zeroRecords: 'Tidak ada data yang cocok dengan pencarian',
        emptyTable: 'Belum ada data tersedia pada tabel ini',
        paginate: {
          first: '<i class="fa-solid fa-angles-left"></i>',
          last: '<i class="fa-solid fa-angles-right"></i>',
          next: '<i class="fa-solid fa-angle-right"></i>',
          previous: '<i class="fa-solid fa-angle-left"></i>'
        }
      }
    });
  });
});
