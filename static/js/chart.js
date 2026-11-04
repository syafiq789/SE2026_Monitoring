window.SE2026Charts = (() => {
  const colors = {
    brown: "#6d3212",
    orange: "#d96616",
    gold: "#dba63a",
    cream: "#ead9c7",
    green: "#25835b",
    red: "#bf3f32",
    blue: "#5c809b",
    mutedBrown: "#9b6b52",
  };

  const chartInstances = {};

  Chart.defaults.font.family =
    "Inter, Segoe UI, sans-serif";

  Chart.defaults.color = "#776b64";

  function numberValue(value) {
    const result = Number(value);

    return Number.isFinite(result)
      ? result
      : 0;
  }

  function encodeValue(value) {
    return encodeURIComponent(
      String(value || ""),
    );
  }

  function normalizeSortDirection(value) {
    return value === "desc"
      ? "desc"
      : value === "asc"
        ? "asc"
        : null;
  }

  function sortProgressItems(
    items,
    direction,
  ) {
    const normalizedDirection =
      normalizeSortDirection(direction);

    if (!normalizedDirection) {
      return items;
    }

    items.sort((first, second) => {
      const difference =
        first.progress - second.progress;

      return normalizedDirection === "desc"
        ? -difference
        : difference;
    });

    return items;
  }

  function openPage(url) {
    if (url) {
      window.location.href = url;
    }
  }

  function destroyOldChart(id) {
    if (chartInstances[id]) {
      chartInstances[id].destroy();
      delete chartInstances[id];
    }

    const canvas =
      document.getElementById(id);

    if (
      canvas &&
      typeof Chart.getChart === "function"
    ) {
      const chart =
        Chart.getChart(canvas);

      if (chart) {
        chart.destroy();
      }
    }
  }

  function getChartBox(canvas) {
    return (
      canvas.closest(".chart-canvas-box") ||
      canvas.parentElement
    );
  }

  function setVerticalChartWidth(
    canvas,
    totalItems,
  ) {
    const box = getChartBox(canvas);

    if (!box) {
      return;
    }

    /*
     * Ruang lebih lebar agar label progress
     * di atas batang tidak saling menumpuk.
     */
    const width = Math.max(
      760,
      totalItems * 66,
    );

    box.style.width = `${width}px`;
    box.style.minWidth = `${width}px`;
    box.style.height = "320px";
  }

  function setHorizontalChartHeight(
    canvas,
    totalItems,
    minimum = 300,
  ) {
    const box = getChartBox(canvas);

    if (!box) {
      return minimum;
    }

    /*
     * Setiap data mendapat ruang vertikal
     * supaya nama dan nilai tetap terbaca.
     *
     * Tinggi dibatasi (maxHeight) karena browser
     * gagal menggambar canvas yang terlalu tinggi
     * (>32000px), yang terjadi saat jumlah data
     * sangat banyak (misal ratusan/ribuan PCL).
     * Jika melebihi batas, box dibuat scrollable.
     */
    const maxHeight = 12000;

    const height = Math.min(
      Math.max(
        minimum,
        totalItems * 34,
      ),
      maxHeight,
    );

    box.style.width = "100%";
    box.style.minWidth = "100%";
    box.style.height = `${height}px`;
    box.style.overflowY =
      totalItems * 34 > maxHeight
        ? "auto"
        : "visible";

    return height;
  }

  function setCursor(
    canvas,
    event,
    activeElements,
  ) {
    const target =
      event?.native?.target ||
      event?.chart?.canvas ||
      canvas;

    if (!target) {
      return;
    }

    target.style.cursor =
      activeElements.length > 0
        ? "pointer"
        : "default";
  }

  function normalizeProgressItems(items) {
    if (!Array.isArray(items)) {
      return [];
    }

    return items.map((item) => ({
      ...item,
      label: item.label || "-",
      progress: numberValue(
        item.progress,
      ),
    }));
  }

  function formatPercentage(value) {
    return `${numberValue(value).toFixed(1)}%`;
  }

  function formatNumber(value) {
    return numberValue(value)
      .toLocaleString("id-ID");
  }

  function formatCompactNumber(value) {
    const number =
      numberValue(value);

    if (number < 1000) {
      return formatNumber(number);
    }

    return new Intl.NumberFormat(
      "id-ID",
      {
        notation: "compact",
        maximumFractionDigits: 1,
      },
    ).format(number);
  }

  function roundedRect(
    ctx,
    x,
    y,
    width,
    height,
    radius,
  ) {
    if (
      typeof ctx.roundRect === "function"
    ) {
      ctx.beginPath();
      ctx.roundRect(
        x,
        y,
        width,
        height,
        radius,
      );
      return;
    }

    const r = Math.min(
      radius,
      width / 2,
      height / 2,
    );

    ctx.beginPath();
    ctx.moveTo(x + r, y);
    ctx.lineTo(x + width - r, y);
    ctx.quadraticCurveTo(
      x + width,
      y,
      x + width,
      y + r,
    );
    ctx.lineTo(
      x + width,
      y + height - r,
    );
    ctx.quadraticCurveTo(
      x + width,
      y + height,
      x + width - r,
      y + height,
    );
    ctx.lineTo(x + r, y + height);
    ctx.quadraticCurveTo(
      x,
      y + height,
      x,
      y + height - r,
    );
    ctx.lineTo(x, y + r);
    ctx.quadraticCurveTo(
      x,
      y,
      x + r,
      y,
    );
    ctx.closePath();
  }

  /*
   * Plugin universal untuk menampilkan nilai secara permanen
   * pada semua grafik batang dashboard.
   */
  const permanentValueLabelsPlugin = {
    id: "permanentValueLabels",

    afterDatasetsDraw(
      chart,
      args,
      pluginOptions,
    ) {
      if (
        chart.config.type !== "bar" ||
        !pluginOptions ||
        pluginOptions.display === false
      ) {
        return;
      }

      const datasetIndex =
        pluginOptions.datasetIndex ?? 0;

      const meta =
        chart.getDatasetMeta(
          datasetIndex,
        );

      const dataset =
        chart.data.datasets[
          datasetIndex
        ];

      if (
        !meta ||
        meta.hidden ||
        !dataset ||
        !Array.isArray(meta.data)
      ) {
        return;
      }

      const ctx = chart.ctx;
      const chartArea = chart.chartArea;

      const orientation =
        pluginOptions.orientation ||
        (
          chart.options.indexAxis === "y"
            ? "horizontal"
            : "vertical"
        );

      const valueType =
        pluginOptions.valueType ||
        "percentage";

      const fontSize =
        pluginOptions.fontSize || 8;

      const fontWeight =
        pluginOptions.fontWeight || 700;

      const backgroundColor =
        pluginOptions.backgroundColor ||
        "#ffffff";

      const borderColor =
        pluginOptions.borderColor ||
        dataset.borderColor ||
        dataset.backgroundColor ||
        colors.orange;

      const textColor =
        pluginOptions.textColor ||
        colors.brown;

      const formatter =
        typeof pluginOptions.formatter
          === "function"
          ? pluginOptions.formatter
          : (value) => {
              if (
                valueType === "number"
              ) {
                return pluginOptions.compact
                  ? formatCompactNumber(value)
                  : formatNumber(value);
              }

              return formatPercentage(value);
            };

      ctx.save();
      ctx.font =
        `${fontWeight} ${fontSize}px ` +
        "Inter, Segoe UI, sans-serif";
      ctx.textAlign = "center";
      ctx.textBaseline = "middle";

      meta.data.forEach(
        (element, index) => {
          const value =
            numberValue(
              dataset.data[index],
            );

          const label =
            formatter(
              value,
              index,
              chart,
            );

          if (
            label === null ||
            label === undefined ||
            label === ""
          ) {
            return;
          }

          const measured =
            ctx.measureText(
              String(label),
            );

          const boxWidth =
            Math.max(
              34,
              measured.width + 10,
            );

          const boxHeight =
            pluginOptions.boxHeight ||
            17;

          const radius = 5;

          let centerX;
          let centerY;
          let currentTextColor =
            textColor;

          if (
            orientation === "horizontal"
          ) {
            const outsideX =
              element.x +
              boxWidth / 2 +
              7;

            const canPlaceOutside =
              outsideX +
              boxWidth / 2 <=
              chartArea.right - 2;

            if (canPlaceOutside) {
              centerX = outsideX;
              centerY = element.y;
            } else {
              /*
               * Jika batang hampir menyentuh batas kanan,
               * label diletakkan di dalam ujung batang.
               */
              centerX =
                Math.max(
                  chartArea.left +
                    boxWidth / 2 +
                    2,
                  element.x -
                    boxWidth / 2 -
                    5,
                );

              centerY = element.y;
              currentTextColor =
                "#ffffff";
            }
          } else {
            centerX = element.x;
            centerY =
              element.y -
              boxHeight / 2 -
              6;
          }

          centerX = Math.max(
            chartArea.left +
              boxWidth / 2,
            Math.min(
              centerX,
              chartArea.right -
                boxWidth / 2,
            ),
          );

          centerY = Math.max(
            chartArea.top -
              boxHeight / 2 -
              1,
            Math.min(
              centerY,
              chartArea.bottom -
                boxHeight / 2,
            ),
          );

          const left =
            centerX -
            boxWidth / 2;

          const top =
            centerY -
            boxHeight / 2;

          roundedRect(
            ctx,
            left,
            top,
            boxWidth,
            boxHeight,
            radius,
          );

          if (
            currentTextColor ===
            "#ffffff"
          ) {
            ctx.fillStyle =
              borderColor;
            ctx.fill();
          } else {
            ctx.fillStyle =
              backgroundColor;
            ctx.fill();

            ctx.lineWidth = 1;
            ctx.strokeStyle =
              borderColor;
            ctx.stroke();
          }

          ctx.fillStyle =
            currentTextColor;

          ctx.fillText(
            String(label),
            centerX,
            centerY,
          );
        },
      );

      ctx.restore();
    },
  };

  /*
   * Menampilkan progress keseluruhan di tengah doughnut.
   */
  const doughnutCenterLabelPlugin = {
    id: "doughnutCenterLabel",

    afterDraw(
      chart,
      args,
      pluginOptions,
    ) {
      if (
        !pluginOptions ||
        pluginOptions.display === false ||
        chart.config.type !== "doughnut"
      ) {
        return;
      }

      const dataset =
        chart.data.datasets[0];

      if (!dataset) {
        return;
      }

      const values =
        dataset.data.map(
          numberValue,
        );

      const total =
        values.reduce(
          (sum, value) =>
            sum + value,
          0,
        );

      const processed =
        values[0] || 0;

      const percentage =
        total > 0
          ? (
              processed /
              total *
              100
            )
          : 0;

      const meta =
        chart.getDatasetMeta(0);

      const firstArc =
        meta.data[0];

      if (!firstArc) {
        return;
      }

      const ctx = chart.ctx;
      const x = firstArc.x;
      const y = firstArc.y;

      ctx.save();
      ctx.textAlign = "center";
      ctx.textBaseline = "middle";

      ctx.fillStyle =
        colors.brown;
      ctx.font =
        "800 18px Inter, Segoe UI, sans-serif";
      ctx.fillText(
        `${percentage.toFixed(1)}%`,
        x,
        y - 5,
      );

      ctx.fillStyle =
        "#776b64";
      ctx.font =
        "600 9px Inter, Segoe UI, sans-serif";
      ctx.fillText(
        "Progress",
        x,
        y + 13,
      );

      ctx.restore();
    },
  };

  Chart.register(
    permanentValueLabelsPlugin,
    doughnutCenterLabelPlugin,
  );

  function createVerticalProgressChart({
    id,
    items,
    color,
    createUrl,
    scroll = false,
    sortDirection = null,
  }) {
    const canvas =
      document.getElementById(id);

    if (!canvas) {
      return;
    }

    const chartItems =
      normalizeProgressItems(items);

    sortProgressItems(
      chartItems,
      sortDirection,
    );

    if (scroll) {
      setVerticalChartWidth(
        canvas,
        chartItems.length,
      );
    }

    destroyOldChart(id);

    chartInstances[id] = new Chart(
      canvas,
      {
        type: "bar",

        data: {
          labels: chartItems.map(
            (item) => item.label,
          ),

          datasets: [
            {
              label: "Progress",
              data: chartItems.map(
                (item) =>
                  item.progress,
              ),
              backgroundColor:
                color,
              borderColor:
                color,
              borderWidth: 1,
              borderRadius: 6,
              borderSkipped: false,
              maxBarThickness: 30,
              categoryPercentage:
                0.82,
              barPercentage:
                0.84,
            },
          ],
        },

        options: {
          responsive: true,
          maintainAspectRatio: false,

          layout: {
            padding: {
              top: 34,
              left: 4,
              right: 4,
            },
          },

          interaction: {
            mode: "nearest",
            intersect: true,
          },

          onHover(
            event,
            activeElements,
          ) {
            setCursor(
              canvas,
              event,
              activeElements,
            );
          },

          onClick(
            event,
            activeElements,
          ) {
            if (
              !activeElements.length ||
              typeof createUrl
                !== "function"
            ) {
              return;
            }

            const index =
              activeElements[0]
                .index;

            const selected =
              chartItems[index];

            if (selected) {
              openPage(
                createUrl(
                  selected,
                ),
              );
            }
          },

          plugins: {
            permanentValueLabels: {
              display: true,
              orientation:
                "vertical",
              valueType:
                "percentage",
              fontSize: 8,
              borderColor:
                color,
            },

            legend: {
              display: false,
            },

            tooltip: {
              callbacks: {
                title(context) {
                  const index =
                    context[0]
                      ?.dataIndex;

                  const label =
                    chartItems[index]
                      ?.label || "-";

                  const value =
                    numberValue(
                      context[0]
                        ?.raw,
                    );

                  return (
                    `${label} · ` +
                    `${value.toFixed(2)}%`
                  );
                },

                label() {
                  return null;
                },
              },
            },
          },

          scales: {
            y: {
              beginAtZero: true,
              min: 0,
              max: 100,

              grid: {
                color:
                  "#eee5dc",
              },

              ticks: {
                callback(value) {
                  return `${value}%`;
                },
              },
            },

            x: {
              grid: {
                display: false,
              },

              ticks: {
                autoSkip: false,
                maxRotation: 50,
                minRotation: 25,

                font: {
                  size: 10,
                },
              },
            },
          },
        },
      },
    );
  }

  /*
   * Chart PCL menggunakan tampilan list HTML (bukan
   * canvas Chart.js), karena jumlah PCL bisa mencapai
   * ribuan baris. Canvas Chart.js gagal digambar bila
   * tingginya melebihi batas browser, sedangkan list
   * HTML biasa tidak punya batas tinggi tersebut dan
   * tetap ringan untuk di-scroll.
   */
  function createProgressListChart({
    id,
    items,
    createUrl,
    sortDirection = null,
  }) {
    const container =
      document.getElementById(id);

    if (!container) {
      return;
    }

    const chartItems =
      normalizeProgressItems(items);

    sortProgressItems(
      chartItems,
      sortDirection,
    );

    container.innerHTML = "";

    chartItems.forEach((item) => {
      const row =
        document.createElement("div");

      row.className =
        "progress-list-row";

      const name =
        document.createElement("div");

      name.className =
        "progress-list-name";

      name.textContent = item.label;

      const track =
        document.createElement("div");

      track.className =
        "progress-list-track";

      const fill =
        document.createElement("div");

      fill.className =
        "progress-list-fill";

      const clampedProgress =
        Math.max(
          0,
          Math.min(100, item.progress),
        );

      fill.style.width =
        `${clampedProgress}%`;

      const value =
        document.createElement("span");

      value.className =
        "progress-list-value";

      value.textContent =
        formatPercentage(
          item.progress,
        );

      fill.appendChild(value);
      track.appendChild(fill);
      row.appendChild(name);
      row.appendChild(track);

      if (
        typeof createUrl === "function"
      ) {
        row.addEventListener(
          "click",
          () => {
            openPage(
              createUrl(item),
            );
          },
        );
      }

      container.appendChild(row);
    });
  }

  function createHorizontalProgressChart({
    id,
    items,
    color,
    createUrl,
    sortDirection = null,
  }) {
    const canvas =
      document.getElementById(id);

    if (!canvas) {
      return;
    }

    const chartItems =
      normalizeProgressItems(items);

    sortProgressItems(
      chartItems,
      sortDirection,
    );

    const finalHeight =
      setHorizontalChartHeight(
        canvas,
        chartItems.length,
      );

    /*
     * Ketebalan batang menyesuaikan ruang yang
     * benar-benar tersedia, supaya batang tidak
     * saling tumpang tindih saat jumlah data
     * sangat banyak.
     */
    const perItemSpace =
      finalHeight / chartItems.length;

    const dynamicThickness = Math.max(
      2,
      Math.min(20, perItemSpace - 4),
    );

    destroyOldChart(id);

    chartInstances[id] = new Chart(
      canvas,
      {
        type: "bar",

        data: {
          labels: chartItems.map(
            (item) =>
              item.label,
          ),

          datasets: [
            {
              label: "Progress",
              data: chartItems.map(
                (item) =>
                  item.progress,
              ),
              backgroundColor:
                color,
              borderColor:
                color,
              borderWidth: 1,
              borderRadius: 6,
              borderSkipped: false,
              barThickness:
                dynamicThickness,
              maxBarThickness:
                dynamicThickness,
            },
          ],
        },

        options: {
          indexAxis: "y",
          responsive: true,
          maintainAspectRatio: false,

          layout: {
            padding: {
              right: 52,
            },
          },

          interaction: {
            mode: "nearest",
            intersect: true,
          },

          onHover(
            event,
            activeElements,
          ) {
            setCursor(
              canvas,
              event,
              activeElements,
            );
          },

          onClick(
            event,
            activeElements,
          ) {
            if (
              !activeElements.length ||
              typeof createUrl
                !== "function"
            ) {
              return;
            }

            const index =
              activeElements[0]
                .index;

            const selected =
              chartItems[index];

            if (selected) {
              openPage(
                createUrl(
                  selected,
                ),
              );
            }
          },

          plugins: {
            permanentValueLabels: {
              display: true,
              orientation:
                "horizontal",
              valueType:
                "percentage",
              fontSize: 8,
              borderColor:
                color,
            },

            legend: {
              display: false,
            },

            tooltip: {
              callbacks: {
                title(context) {
                  const index =
                    context[0]
                      ?.dataIndex;

                  const label =
                    chartItems[index]
                      ?.label || "-";

                  const value =
                    numberValue(
                      context[0]
                        ?.raw,
                    );

                  return (
                    `${label} · ` +
                    `${value.toFixed(2)}%`
                  );
                },

                label() {
                  return null;
                },
              },
            },
          },

          scales: {
            x: {
              beginAtZero: true,
              min: 0,
              max: 100,

              grid: {
                color:
                  "#eee5dc",
              },

              ticks: {
                callback(value) {
                  return `${value}%`;
                },
              },
            },

            y: {
              grid: {
                display: false,
              },

              ticks: {
                autoSkip: false,

                font: {
                  size: 10,
                },
              },
            },
          },
        },
      },
    );
  }

  function createUploadChart(
    summary,
  ) {
    const canvas =
      document.getElementById(
        "uploadChart",
      );

    if (!canvas) {
      return;
    }

    const uploadItems = [
      {
        label:
          "Sudah Upload",
        value: numberValue(
          summary.total_processed,
        ),
        url:
          "/monitoring-sls",
      },
      {
        label:
          "Belum Upload",
        value: numberValue(
          summary.total_remaining,
        ),
        url:
          "/monitoring-sls",
      },
    ];

    destroyOldChart(
      "uploadChart",
    );

    chartInstances.uploadChart =
      new Chart(
        canvas,
        {
          type: "doughnut",

          data: {
            labels:
              uploadItems.map(
                (item) =>
                  item.label,
              ),

            datasets: [
              {
                data:
                  uploadItems.map(
                    (item) =>
                      item.value,
                  ),

                backgroundColor: [
                  colors.green,
                  colors.cream,
                ],

                borderWidth: 0,
              },
            ],
          },

          options: {
            responsive: true,
            maintainAspectRatio:
              false,
            cutout: "72%",

            layout: {
              padding: {
                top: 4,
                left: 8,
                right: 8,
                bottom: 4,
              },
            },

            interaction: {
              mode: "nearest",
              intersect: true,
            },

            onHover(
              event,
              activeElements,
            ) {
              setCursor(
                canvas,
                event,
                activeElements,
              );
            },

            onClick(
              event,
              activeElements,
            ) {
              if (
                !activeElements.length
              ) {
                return;
              }

              const index =
                activeElements[0]
                  .index;

              openPage(
                uploadItems[index]
                  ?.url,
              );
            },

            plugins: {
              doughnutCenterLabel: {
                display: true,
              },

              legend: {
                position: "bottom",

                labels: {
                  usePointStyle: true,
                  padding: 18,

                  generateLabels(
                    chart,
                  ) {
                    const dataset =
                      chart.data
                        .datasets[0];

                    return chart.data
                      .labels
                      .map(
                        (
                          label,
                          index,
                        ) => ({
                          text:
                            `${label} · ` +
                            formatNumber(
                              dataset.data[
                                index
                              ],
                            ),

                          fillStyle:
                            dataset
                              .backgroundColor[
                                index
                              ],

                          strokeStyle:
                            dataset
                              .backgroundColor[
                                index
                              ],

                          pointStyle:
                            "circle",

                          hidden: false,
                          index,
                        }),
                      );
                  },
                },

                onClick(
                  event,
                  item,
                ) {
                  openPage(
                    uploadItems[
                      item.index
                    ]?.url,
                  );
                },
              },

              tooltip: {
                enabled: false,
              },
            },
          },
        },
      );
  }

  function createWorkflowChart(
    items,
  ) {
    const canvas =
      document.getElementById(
        "workflowChart",
      );

    if (!canvas) {
      return;
    }

    let workflowItems;

    if (Array.isArray(items)) {
      workflowItems =
        items.map(
          (item) => ({
            key:
              item.key ||
              item.label ||
              "-",

            label:
              item.label ||
              item.key ||
              "-",

            value:
              numberValue(
                item.value,
              ),
          }),
        );
    } else if (
      items &&
      typeof items === "object"
    ) {
      workflowItems =
        Object.entries(
          items,
        ).map(
          ([key, value]) => ({
            key,
            label: key,
            value:
              numberValue(
                value,
              ),
          }),
        );
    } else {
      workflowItems = [];
    }

    const workflowColors = {
      APPROVED:
        colors.brown,
      COMPLETED:
        colors.gold,
      DRAFT:
        colors.green,
      EDITED:
        colors.orange,
      OPEN:
        colors.cream,
      REJECTED:
        colors.red,
      REVOKED:
        colors.mutedBrown,
      SUBMITTED:
        colors.blue,
    };

    destroyOldChart(
      "workflowChart",
    );

    chartInstances.workflowChart =
      new Chart(
        canvas,
        {
          type: "bar",

          data: {
            labels:
              workflowItems.map(
                (item) =>
                  item.label,
              ),

            datasets: [
              {
                label: "Jumlah",

                data:
                  workflowItems.map(
                    (item) =>
                      item.value,
                  ),

                backgroundColor:
                  workflowItems.map(
                    (item) =>
                      workflowColors[
                        item.key
                      ] ||
                      colors.orange,
                  ),

                borderColor:
                  workflowItems.map(
                    (item) =>
                      workflowColors[
                        item.key
                      ] ||
                      colors.orange,
                  ),

                borderWidth: 1,
                borderRadius: 5,
                borderSkipped: false,
                maxBarThickness: 40,
              },
            ],
          },

          options: {
            responsive: true,
            maintainAspectRatio:
              false,

            layout: {
              padding: {
                top: 32,
              },
            },

            interaction: {
              mode: "nearest",
              intersect: true,
            },

            onHover(
              event,
              activeElements,
            ) {
              setCursor(
                canvas,
                event,
                activeElements,
              );
            },

            onClick(
              event,
              activeElements,
            ) {
              if (
                !activeElements.length
              ) {
                return;
              }

              const index =
                activeElements[0]
                  .index;

              const selected =
                workflowItems[index];

              openPage(
                "/monitoring-sls" +
                "?workflow=" +
                encodeValue(
                  selected?.key ||
                  "",
                ),
              );
            },

            plugins: {
              permanentValueLabels: {
                display: true,
                orientation:
                  "vertical",
                valueType:
                  "number",
                compact: true,
                fontSize: 8,
                borderColor:
                  colors.orange,
              },

              legend: {
                display: false,
              },

              tooltip: {
                callbacks: {
                  title(
                    context,
                  ) {
                    const index =
                      context[0]
                        ?.dataIndex;

                    const label =
                      workflowItems[
                        index
                      ]?.label ||
                      "-";

                    const value =
                      numberValue(
                        context[0]
                          ?.raw,
                      );

                    return (
                      `${label} · ` +
                      formatNumber(
                        value,
                      )
                    );
                  },

                  label() {
                    return null;
                  },
                },
              },
            },

            scales: {
              y: {
                beginAtZero: true,

                grid: {
                  color:
                    "#eee5dc",
                },

                ticks: {
                  callback(value) {
                    return formatCompactNumber(
                      value,
                    );
                  },
                },
              },

              x: {
                grid: {
                  display: false,
                },

                ticks: {
                  autoSkip: false,
                  maxRotation: 45,
                  minRotation: 25,
                },
              },
            },
          },
        },
      );
  }

  function render(
    data,
    summary,
  ) {
    const chartData =
      data || {};

    const summaryData =
      summary || {};

    const sortDirection =
      normalizeSortDirection(
        chartData.sort_order,
      );

    createUploadChart(
      summaryData,
    );

    createVerticalProgressChart({
      id: "kecamatanChart",
      items:
        chartData.kecamatan,
      color:
        colors.orange,
      scroll: true,
      sortDirection,

      createUrl(item) {
        if (!item.kec_code) {
          return (
            "/monitoring-kecamatan"
          );
        }

        return (
          "/monitoring-kecamatan" +
          "?kec_code=" +
          encodeValue(
            item.kec_code,
          )
        );
      },
    });

    createWorkflowChart(
      chartData.workflow,
    );

    createHorizontalProgressChart({
      id: "pmlChart",
      items:
        chartData.pml,
      color:
        colors.orange,
      sortDirection,

      createUrl(item) {
        if (!item.pml_id) {
          return (
            "/monitoring-pml"
          );
        }

        return (
          "/monitoring-pml" +
          "?pml_id=" +
          encodeValue(
            item.pml_id,
          )
        );
      },
    });

    /*
     * PCL memakai tampilan list HTML (createProgressListChart),
     * bukan chart canvas, karena jumlah PCL bisa sangat banyak
     * (ratusan hingga ribuan baris).
     */
    createProgressListChart({
      id: "pclChart",
      items:
        chartData.pcl,
      sortDirection,

      createUrl(item) {
        if (!item.pcl_id) {
          return (
            "/monitoring-pcl"
          );
        }

        return (
          "/monitoring-pcl" +
          "?pcl_id=" +
          encodeValue(
            item.pcl_id,
          )
        );
      },
    });

    createHorizontalProgressChart({
      id: "lowKecChart",

      items:
        chartData
          .kecamatan_terendah ||
        chartData.kecamatan,

      color:
        colors.red,
      sortDirection,

      createUrl(item) {
        if (!item.kec_code) {
          return (
            "/monitoring-kecamatan"
          );
        }

        return (
          "/monitoring-kecamatan" +
          "?kec_code=" +
          encodeValue(
            item.kec_code,
          )
        );
      },
    });

    createHorizontalProgressChart({
      id: "lowPmlChart",
      items:
        chartData.pml_terendah,
      color:
        colors.gold,

      /*
       * Grafik ini tetap khusus
       * 10 PML terendah.
       */
      sortDirection: "asc",

      createUrl(item) {
        if (!item.pml_id) {
          return (
            "/monitoring-pml"
          );
        }

        return (
          "/monitoring-pml" +
          "?pml_id=" +
          encodeValue(
            item.pml_id,
          )
        );
      },
    });
  }

  return {
    render,
  };
})();