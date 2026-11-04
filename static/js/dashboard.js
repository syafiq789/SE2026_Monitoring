document.addEventListener(
  "DOMContentLoaded",
  async () => {
    const kecamatanFilter =
      document.getElementById(
        "dashboardKecamatanFilter",
      );

    const pmlFilter =
      document.getElementById(
        "dashboardPmlFilter",
      );

    const pclFilter =
      document.getElementById(
        "dashboardPclFilter",
      );

    const applyButton =
      document.getElementById(
        "applyDashboardFilter",
      );

    const resetButton =
      document.getElementById(
        "resetDashboardFilter",
      );

    const filterInfo =
      document.getElementById(
        "dashboardFilterInfo",
      );

    const filterToggle =
      document.getElementById(
        "dashboardFilterToggle",
      );

    const filterPanel =
      document.getElementById(
        "dashboardFilterPanel",
      );

    const filterClose =
      document.getElementById(
        "dashboardFilterClose",
      );

    let originalChartData = null;

    function openFilterPanel() {
      if (!filterPanel) {
        return;
      }

      filterPanel.hidden = false;
      filterToggle?.setAttribute(
        "aria-expanded",
        "true",
      );

      document.body.classList.add(
        "dashboard-filter-open",
      );
    }

    function closeFilterPanel() {
      if (!filterPanel) {
        return;
      }

      filterPanel.hidden = true;
      filterToggle?.setAttribute(
        "aria-expanded",
        "false",
      );

      document.body.classList.remove(
        "dashboard-filter-open",
      );
    }

    function toggleFilterPanel() {
      if (!filterPanel) {
        return;
      }

      if (filterPanel.hidden) {
        openFilterPanel();
      } else {
        closeFilterPanel();
      }
    }

    function numberValue(value) {
      const result = Number(value);

      return Number.isFinite(result)
        ? result
        : 0;
    }

    function stringValue(value) {
      return String(value ?? "");
    }

    function cloneItems(items) {
      return Array.isArray(items)
        ? items.map((item) => ({
            ...item,
          }))
        : [];
    }

    function uniqueBy(items, getKey) {
      const result = new Map();

      items.forEach((item) => {
        const key =
          stringValue(getKey(item));

        if (!key || result.has(key)) {
          return;
        }

        result.set(key, item);
      });

      return Array.from(
        result.values(),
      );
    }

    function compareName(first, second) {
      return stringValue(
        first.label || first.name,
      ).localeCompare(
        stringValue(
          second.label || second.name,
        ),
        "id",
      );
    }

    function resetSelect(
      select,
      firstLabel,
    ) {
      if (!select) {
        return;
      }

      select.innerHTML = "";

      const option =
        document.createElement("option");

      option.value = "";
      option.textContent = firstLabel;

      select.appendChild(option);
    }

    function appendOption(
      select,
      value,
      label,
    ) {
      if (!select) {
        return;
      }

      const option =
        document.createElement("option");

      option.value =
        stringValue(value);

      option.textContent =
        stringValue(label);

      select.appendChild(option);
    }

    function populateKecamatanOptions() {
      resetSelect(
        kecamatanFilter,
        "Semua Kecamatan",
      );

      const items = uniqueBy(
        cloneItems(
          originalChartData?.kecamatan,
        ),
        (item) => item.kec_code,
      ).sort(compareName);

      items.forEach((item) => {
        appendOption(
          kecamatanFilter,
          item.kec_code,
          item.label,
        );
      });
    }

    function getAvailablePml() {
      const selectedKecCode =
        kecamatanFilter?.value || "";

      let items = cloneItems(
        originalChartData?.pml,
      );

      if (selectedKecCode) {
        items = items.filter(
          (item) =>
            stringValue(item.kec_code) ===
            stringValue(selectedKecCode),
        );
      }

      return uniqueBy(
        items,
        (item) => item.pml_id,
      ).sort(compareName);
    }

    function populatePmlOptions() {
      const oldValue =
        pmlFilter?.value || "";

      resetSelect(
        pmlFilter,
        "Semua PML",
      );

      const items =
        getAvailablePml();

      items.forEach((item) => {
        appendOption(
          pmlFilter,
          item.pml_id,
          item.label,
        );
      });

      if (
        pmlFilter &&
        items.some(
          (item) =>
            stringValue(item.pml_id) ===
            stringValue(oldValue),
        )
      ) {
        pmlFilter.value = oldValue;
      }
    }

    function getAvailablePcl() {
      const selectedKecCode =
        kecamatanFilter?.value || "";

      const selectedPmlId =
        pmlFilter?.value || "";

      let items = cloneItems(
        originalChartData?.pcl,
      );

      if (selectedKecCode) {
        items = items.filter(
          (item) =>
            stringValue(item.kec_code) ===
            stringValue(selectedKecCode),
        );
      }

      if (selectedPmlId) {
        items = items.filter(
          (item) =>
            stringValue(item.pml_id) ===
            stringValue(selectedPmlId),
        );
      }

      return uniqueBy(
        items,
        (item) => item.pcl_id,
      ).sort(compareName);
    }

    function populatePclOptions() {
      const oldValue =
        pclFilter?.value || "";

      resetSelect(
        pclFilter,
        "Semua PCL",
      );

      const items =
        getAvailablePcl();

      items.forEach((item) => {
        appendOption(
          pclFilter,
          item.pcl_id,
          item.label,
        );
      });

      if (
        pclFilter &&
        items.some(
          (item) =>
            stringValue(item.pcl_id) ===
            stringValue(oldValue),
        )
      ) {
        pclFilter.value = oldValue;
      }
    }

    function selectedText(
      select,
      fallback,
    ) {
      if (
        !select ||
        !select.value
      ) {
        return fallback;
      }

      return (
        select.options[
          select.selectedIndex
        ]?.textContent || fallback
      );
    }

    function buildFilteredData() {
      const selectedKecCode =
        kecamatanFilter?.value || "";

      const selectedPmlId =
        pmlFilter?.value || "";

      const selectedPclId =
        pclFilter?.value || "";

      let kecamatan =
        cloneItems(
          originalChartData.kecamatan,
        );

      let pml =
        cloneItems(
          originalChartData.pml,
        );

      let pcl =
        cloneItems(
          originalChartData.pcl,
        );

      if (selectedKecCode) {
        kecamatan = kecamatan.filter(
          (item) =>
            stringValue(item.kec_code) ===
            stringValue(selectedKecCode),
        );

        pml = pml.filter(
          (item) =>
            stringValue(item.kec_code) ===
            stringValue(selectedKecCode),
        );

        pcl = pcl.filter(
          (item) =>
            stringValue(item.kec_code) ===
            stringValue(selectedKecCode),
        );
      }

      if (selectedPmlId) {
        pml = pml.filter(
          (item) =>
            stringValue(item.pml_id) ===
            stringValue(selectedPmlId),
        );

        pcl = pcl.filter(
          (item) =>
            stringValue(item.pml_id) ===
            stringValue(selectedPmlId),
        );
      }

      if (selectedPclId) {
        pcl = pcl.filter(
          (item) =>
            stringValue(item.pcl_id) ===
            stringValue(selectedPclId),
        );
      }

      const kecamatanAscending =
        cloneItems(kecamatan)
          .sort(
            (first, second) =>
              numberValue(first.progress) -
              numberValue(second.progress),
          );

      const pmlTerendah =
        cloneItems(pml)
          .sort(
            (first, second) =>
              numberValue(first.progress) -
              numberValue(second.progress),
          )
          .slice(0, 10);

      return {
        ...originalChartData,
        kecamatan,
        pml,
        pcl,
        kecamatan_terendah:
          kecamatanAscending,
        pml_terendah:
          pmlTerendah,
      };
    }

    function updateFilterInformation(
      filteredData,
    ) {
      if (!filterInfo) {
        return;
      }

      filterInfo.textContent =
        `${selectedText(
          kecamatanFilter,
          "Semua Kecamatan",
        )} · ` +
        `${selectedText(
          pmlFilter,
          "Semua PML",
        )} · ` +
        `${selectedText(
          pclFilter,
          "Semua PCL",
        )} · ` +
        `${filteredData.pml.length} PML · ` +
        `${filteredData.pcl.length} PCL`;
    }

    function applyFilters() {
      if (!originalChartData) {
        return;
      }

      const filteredData =
        buildFilteredData();

      updateFilterInformation(
        filteredData,
      );

      window.SE2026Charts.render(
        filteredData,
        window.SE2026_SUMMARY || {},
      );
    }

    function handleKecamatanChange() {
      if (pmlFilter) {
        pmlFilter.value = "";
      }

      if (pclFilter) {
        pclFilter.value = "";
      }

      populatePmlOptions();
      populatePclOptions();
    }

    function handlePmlChange() {
      if (pclFilter) {
        pclFilter.value = "";
      }

      populatePclOptions();
    }

    function resetFilters() {
      if (kecamatanFilter) {
        kecamatanFilter.value = "";
      }

      if (pmlFilter) {
        pmlFilter.value = "";
      }

      if (pclFilter) {
        pclFilter.value = "";
      }

      populatePmlOptions();
      populatePclOptions();
      applyFilters();
    }

    try {
      const response = await fetch(
        "/api/chart-data",
        {
          method: "GET",
          headers: {
            Accept: "application/json",
          },
          credentials: "same-origin",
        },
      );

      if (!response.ok) {
        throw new Error(
          `Data grafik tidak tersedia. Status: ${response.status}`,
        );
      }

      originalChartData =
        await response.json();

      if (
        !window.SE2026Charts ||
        typeof window.SE2026Charts.render
          !== "function"
      ) {
        throw new Error(
          "Fungsi SE2026Charts.render tidak ditemukan.",
        );
      }

      populateKecamatanOptions();
      populatePmlOptions();
      populatePclOptions();
      applyFilters();

      kecamatanFilter?.addEventListener(
        "change",
        handleKecamatanChange,
      );

      pmlFilter?.addEventListener(
        "change",
        handlePmlChange,
      );

      applyButton?.addEventListener(
        "click",
        () => {
          applyFilters();
          closeFilterPanel();
        },
      );

      resetButton?.addEventListener(
        "click",
        resetFilters,
      );

      filterToggle?.addEventListener(
        "click",
        (event) => {
          event.stopPropagation();
          toggleFilterPanel();
        },
      );

      filterPanel?.addEventListener(
        "click",
        (event) => {
          event.stopPropagation();
        },
      );

      filterClose?.addEventListener(
        "click",
        closeFilterPanel,
      );

      document.addEventListener(
        "click",
        () => {
          if (
            filterPanel &&
            !filterPanel.hidden
          ) {
            closeFilterPanel();
          }
        },
      );

      document.addEventListener(
        "keydown",
        (event) => {
          if (event.key === "Escape") {
            closeFilterPanel();
          }
        },
      );
    } catch (error) {
      console.error(
        "Gagal memuat filter dashboard:",
        error,
      );

      if (filterInfo) {
        filterInfo.textContent =
          "Filter dashboard tidak dapat dimuat";
      }
    }
  },
);
