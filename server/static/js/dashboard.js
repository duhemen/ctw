/* CTW Dashboard - Fase 2A.3 (Layer Batas Wilayah) */
(function () {
  "use strict";

  var state = {
    map: null,
    markers: [],
    boundaryLayer: null,
    observationLayer: null,
    observationData: [],
    showObservations: true,
    boundaryData: {},
    budgetChart: null,
    riskChart: null,
    currentRegion: "",
    currentYear: null,
    currentStatus: "aktif",
    showBoundaries: true,
  };
  // ---------- Toast & Loading helpers ----------
  function toast(msg, type) {
    if (window.CTW && window.CTW.toast) {
      window.CTW.toast[type || "info"](msg);
    }
  }
  function showLoading(id) {
    var el = document.getElementById(id);
    if (el) el.classList.add("ctw-loading-overlay--active");
  }
  function hideLoading(id) {
    var el = document.getElementById(id);
    if (el) el.classList.remove("ctw-loading-overlay--active");
  }


  function $(id) { return document.getElementById(id); }

  async function fetchJSON(url) {
    var res = await fetch(url);
    if (!res.ok) throw new Error("HTTP " + res.status);
    return res.json();
  }

  function formatRupiah(juta) {
    if (juta >= 1000000) return "Rp " + (juta / 1000000).toFixed(1) + " T";
    if (juta >= 1000) return "Rp " + (juta / 1000).toFixed(0) + " M";
    return "Rp " + juta.toFixed(0) + " jt";
  }

  // ---------- Peta ----------
  function initMap() {
    state.map = L.map("projectMap", {
      zoomControl: true,
      attributionControl: true,
    }).setView([-2.5489, 118.0149], 5);

    L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
      attribution: "&copy; OpenStreetMap contributors",
      maxZoom: 18,
    }).addTo(state.map);

    state.boundaryLayer = L.geoJSON(null, {
      style: boundaryStyle,
      onEachFeature: onEachBoundary,
    }).addTo(state.map);

    state.observationLayer = L.layerGroup().addTo(state.map);
  }

  function boundaryStyle(feature) {
    var level = feature.properties.level;
    var palette = {
      provinsi:  { color: "#1e3a8a", weight: 2,   fillColor: "#3b82f6", fillOpacity: 0.05 },
      kabupaten: { color: "#7c3aed", weight: 1.5, fillColor: "#a78bfa", fillOpacity: 0.05 },
      kecamatan: { color: "#dc2626", weight: 1,   fillColor: "#f87171", fillOpacity: 0.04 },
      kelurahan: { color: "#ea580c", weight: 0.8, fillColor: "#fb923c", fillOpacity: 0.04 },
    };
    return palette[level] || palette.provinsi;
  }

  function onEachBoundary(feature, layer) {
    var p = feature.properties;
    layer.bindTooltip(
      "<strong>" + p.name + "</strong><br><small>" + p.level + "</small>",
      { sticky: true }
    );
    layer.on({
      mouseover: function (e) {
        var l = e.target;
        l.setStyle({ weight: 3, fillOpacity: 0.18 });
        l.bringToFront();
      },
      mouseout: function (e) {
        state.boundaryLayer.resetStyle(e.target);
      },
      click: function (e) {
        L.DomEvent.stopPropagation(e);
        onBoundaryClick(p);
      },
    });
  }

  function onBoundaryClick(props) {
    var level = props.level;
    var code = props.code;

    // Set dropdown sesuai level
    if (level === "provinsi") {
      $("filterProvinsi").value = code;
      onProvinsiChange();
    } else if (level === "kabupaten") {
      // Set provinsi dulu
      var parentProv = code.substring(0, 2);
      $("filterProvinsi").value = parentProv;
      onProvinsiChange();
      // Setelah load kabupaten selesai, set value
      setTimeout(function () {
        $("filterKabupaten").value = code;
        onKabupatenChange();
      }, 400);
    } else if (level === "kecamatan") {
      var parentProv = code.substring(0, 2);
      var parentKab = code.substring(0, 4);
      $("filterProvinsi").value = parentProv;
      onProvinsiChange();
      setTimeout(function () {
        $("filterKabupaten").value = parentKab;
        onKabupatenChange();
        setTimeout(function () {
          $("filterKecamatan").value = code;
          onKecamatanChange();
        }, 400);
      }, 400);
    }
  }

  async function loadBoundaries(parentCode, level) {
    if (!state.showBoundaries) return;

    var url = "/api/regions/geojson/collection?level=" + level;
    if (parentCode) url += "&parent_code=" + parentCode;

    try {
      var data = await fetchJSON(url);
      state.boundaryLayer.clearLayers();
      state.boundaryLayer.addData(data);

      var count = data.features.length;
      $("boundaryInfo").textContent = count + " " + levelLabel(level).toLowerCase();
      console.log("[boundaries] Loaded " + count + " features for level=" + level + " parent=" + (parentCode || "-"));
    } catch (err) {
      console.error("[boundaries] Failed:", err);
      $("boundaryInfo").textContent = "";
    }
  }

  function levelLabel(level) {
    return ({ provinsi: "Provinsi", kabupaten: "Kabupaten/Kota", kecamatan: "Kecamatan", kelurahan: "Kelurahan/Desa" })[level] || level;
  }

  
  // ---------- OBSERVASI LAPANGAN ----------
  async function loadObservations() {
    if (!state.showObservations) return;
    var url = "/api/observations?limit=500";
    if (state.currentRegion) url += "&region_code=" + encodeURIComponent(state.currentRegion);
    try {
      var data = await fetchJSON(url);
      state.observationData = data;
      renderObservations(data);
    } catch (e) {
      console.error("[observations] fail", e);
    }
  }

  function renderObservations(observations) {
    state.observationLayer.clearLayers();
    var palette = {
      rendah: "#22c55e",
      sedang: "#f59e0b",
      tinggi: "#ef4444",
    };
    observations.forEach(function (o) {
      if (o.latitude == null || o.longitude == null) return;
      var color = palette[o.severity_level] || "#64748b";
      var marker = L.circleMarker([o.latitude, o.longitude], {
        radius: 7,
        fillColor: color,
        color: "#fff",
        weight: 2,
        opacity: 0.9,
        fillOpacity: 0.85,
        dashArray: "3,3",
      });
      var popupHtml =
        '<div style="min-width:200px;">' +
        '<strong>\uD83D\uDCCD ' + (o.variable_name || o.variable_kode) + '</strong><br>' +
        '<small>' + (o.wilayah_name || o.wilayah_kode) + '</small><hr style="margin:6px 0;">' +
        'Severity: <b style="color:' + color + ';">' + o.severity_level.toUpperCase() + '</b> (' + (o.severity_score * 100).toFixed(0) + ')<br>' +
        'Observer: ' + (o.observer || '-') + '<br>' +
        (o.verified ? '<span style="color:#16a34a;">\u2714 Verified</span>' : '<span style="color:#f59e0b;">\u23F3 Belum verified</span>') +
        '<br><small style="color:#64748b;">' + (o.catatan || '').substring(0, 100) + '</small>' +
        '</div>';
      marker.bindPopup(popupHtml);
      marker.bindTooltip(o.variable_name || o.variable_kode, { direction: "top" });
      state.observationLayer.addLayer(marker);
    });
    console.log("[observations] rendered " + observations.length + " points");
  }

  function refreshMapSize() {
    if (state.map) {
      setTimeout(function () { state.map.invalidateSize(); }, 150);
    }
  }

  // ---------- Dropdown Provinsi ----------
  async function loadProvinces() {
    var data = await fetchJSON("/api/regions?level=provinsi");
    var sel = $("filterProvinsi");
    data.forEach(function (r) {
      var opt = document.createElement("option");
      opt.value = r.code;
      opt.textContent = r.name;
      opt.dataset.lat = r.latitude;
      opt.dataset.lng = r.longitude;
      sel.appendChild(opt);
    });
  }

  async function loadChildren(level, parentCode, targetId) {
    var sel = $(targetId);
    sel.innerHTML = '<option value="">— ' + levelLabel(level) + ' —</option>';
    sel.disabled = true;
    if (!parentCode) return;
    var data = await fetchJSON("/api/regions?level=" + level + "&parent_code=" + parentCode);
    data.forEach(function (r) {
      var opt = document.createElement("option");
      opt.value = r.code;
      opt.textContent = r.name;
      opt.dataset.lat = r.latitude;
      opt.dataset.lng = r.longitude;
      sel.appendChild(opt);
    });
    sel.disabled = false;
  }

  // ---------- Cascade handlers ----------
  function onProvinsiChange() {
    var code = $("filterProvinsi").value;
    resetBelow("kabupaten");
    if (code) {
      loadChildren("kabupaten", code, "filterKabupaten");
      state.currentRegion = code;
      loadDashboard();
      loadBoundaries(code, "kabupaten");
    } else {
      resetToDefault();
      loadBoundaries(null, "provinsi");
    }
  }

  function onKabupatenChange() {
    var code = $("filterKabupaten").value;
    resetBelow("kecamatan");
    if (code) {
      loadChildren("kecamatan", code, "filterKecamatan");
      state.currentRegion = code;
      loadDashboard();
      loadBoundaries(code, "kecamatan");
    } else if ($("filterProvinsi").value) {
      var provCode = $("filterProvinsi").value;
      state.currentRegion = provCode;
      loadDashboard();
      loadBoundaries(provCode, "kabupaten");
    }
  }

  function onKecamatanChange() {
    var code = $("filterKecamatan").value;
    resetBelow("kelurahan");
    if (code) {
      loadChildren("kelurahan", code, "filterKelurahan");
      state.currentRegion = code;
      loadDashboard();
      loadBoundaries(code, "kelurahan");
    } else if ($("filterKabupaten").value) {
      var kabCode = $("filterKabupaten").value;
      state.currentRegion = kabCode;
      loadDashboard();
      loadBoundaries(kabCode, "kecamatan");
    }
  }

  function onKelurahanChange() {
    var code = $("filterKelurahan").value;
    if (code) {
      state.currentRegion = code;
      loadDashboard();
    } else if ($("filterKecamatan").value) {
      var kecCode = $("filterKecamatan").value;
      state.currentRegion = kecCode;
      loadDashboard();
    }
  }

  function resetBelow(level) {
    var map = { kabupaten: "filterKabupaten", kecamatan: "filterKecamatan", kelurahan: "filterKelurahan" };
    var startIdx = ["kabupaten", "kecamatan", "kelurahan"].indexOf(level);
    ["kabupaten", "kecamatan", "kelurahan"].slice(startIdx).forEach(function (lvl) {
      var el = $(map[lvl]);
      el.innerHTML = '<option value="">— ' + levelLabel(lvl) + ' —</option>';
      el.disabled = true;
    });
  }

  function resetToDefault() {
    state.currentRegion = "";
    $("filterProvinsi").value = "";
    $("filterTahun").value = "";
    resetBelow("kabupaten");
    clearMarkers();
    if (state.observationLayer) state.observationLayer.clearLayers();
    if (state.map) state.map.setView([-2.5489, 118.0149], 5);

    $("statProjects").textContent = "-";
    $("statBudget").textContent = "-";
    $("statAudit").textContent = "-";
    $("statPublic").textContent = "-";

    $("mapHint").style.display = "block";
    $("budgetHint").style.display = "flex";
    $("riskHint").style.display = "flex";

    clearCharts();

    $("providerTable").querySelector("tbody").innerHTML =
      '<tr><td colspan="6" class="ctw-empty">Pilih wilayah untuk menampilkan data.</td></tr>';
    $("blacklistTable").querySelector("tbody").innerHTML =
      '<tr><td colspan="7" class="ctw-empty">Belum ada data blacklist.</td></tr>';

    loadBoundaries(null, "provinsi");
  }

  // ---------- Dashboard ----------
  async function loadDashboard() {
    if (!state.currentRegion) return;
    showLoading("mapLoading");
    showLoading("budgetLoading");
    showLoading("riskLoading");
    var url = "/api/dashboard?region_code=" + encodeURIComponent(state.currentRegion);
    if (state.currentYear) url += "&year=" + state.currentYear;
    if (state.currentStatus && state.currentStatus !== "aktif") url += "&status=" + encodeURIComponent(state.currentStatus);
    else url += "&status=aktif";
    var data = await fetchJSON(url);

    $("mapHint").style.display = "none";
    $("budgetHint").style.display = "none";
    $("riskHint").style.display = "none";

    $("statProjects").textContent = data.total_projects;
    $("statBudget").textContent = data.total_budget_str;
    $("statAudit").textContent = data.active_audits;
    $("statPublic").textContent = data.public_reports;

    renderMapMarkers(data.projects);
    zoomToRegion();
    refreshMapSize();

    renderCharts(data.budget_data, data.risk_distribution);

    await loadProviders();
    await loadBlacklist();
    await loadObservations();
    hideLoading("mapLoading");
    hideLoading("budgetLoading");
    hideLoading("riskLoading");
  }

  function zoomToRegion() {
    var code = state.currentRegion;
    var selects = ["filterProvinsi", "filterKabupaten", "filterKecamatan", "filterKelurahan"];
    for (var i = 0; i < selects.length; i++) {
      var sel = $(selects[i]);
      var opt = sel.querySelector('option[value="' + code + '"]');
      if (opt && opt.dataset.lat && opt.dataset.lng) {
        var lat = parseFloat(opt.dataset.lat);
        var lng = parseFloat(opt.dataset.lng);
        if (!isNaN(lat) && !isNaN(lng)) {
          var level = sel.id.replace("filter", "").toLowerCase();
          var zoom = ({ provinsi: 7, kabupaten: 9, kecamatan: 11, kelurahan: 13 })[level] || 10;
          state.map.setView([lat, lng], zoom);
        }
        return;
      }
    }
  }

  function clearMarkers() {
    state.markers.forEach(function (m) { state.map.removeLayer(m); });
    state.markers = [];
  }

  function renderMapMarkers(projects) {
    clearMarkers();
    var riskColor = { Rendah: "#22c55e", Sedang: "#f59e0b", Tinggi: "#ef4444" };
    var statusStyle = {
      Berjalan:     { color: "#22c55e", icon: "\u25CF", label: "Berjalan" },
      Perencanaan:  { color: "#3b82f6", icon: "\u25CB", label: "Perencanaan" },
      Selesai:      { color: "#64748b", icon: "\u2714", label: "Selesai" },
      Ditunda:      { color: "#f59e0b", icon: "\u23F8", label: "Ditunda" },
      Dibatalkan:   { color: "#ef4444", icon: "\u2716", label: "Dibatalkan" },
    };

    projects.forEach(function (p) {
      var color = riskColor[p.risk] || "#3b82f6";
      var st = statusStyle[p.status] || statusStyle.Berjalan;
      var marker = L.circleMarker([p.lat, p.lng], {
        radius: 11, fillColor: color, color: st.color, weight: 3,
        opacity: 1, fillOpacity: 0.9,
      }).addTo(state.map);

      var popupHtml =
        '<div style="min-width:180px;">' +
        '<strong>' + p.name + '</strong><br>' +
        '<small>' + (p.provider || "-") + '</small><hr style="margin:6px 0;">' +
        'Status: <b style="color:' + st.color + ';">' + st.icon + ' ' + st.label + '</b><br>' +
        'Risiko: <span style="color:' + color + ';font-weight:bold;">' + p.risk + '</span><br>' +
        'Nilai: <b>' + formatRupiah(p.contract_value || 0) + '</b><br>' +
        'Progres: <b>' + (p.progress_physical || 0).toFixed(1) + '%</b>' +
        '<br><button onclick="window.__ctwOpenDetail(' + p.id + ')" ' +
        'style="margin-top:6px;padding:4px 10px;border:none;background:#1e3a8a;' +
        'color:#fff;border-radius:4px;cursor:pointer;font-size:12px;">Lihat Detail</button>' +
        '</div>';

      marker.bindPopup(popupHtml);
      marker.on("click", function () { window.__ctwOpenDetail(p.id); });
      state.markers.push(marker);
    });
  }

  function renderCharts(budget, risk) {
    clearCharts();
    state.budgetChart = new Chart($("budgetChart"), {
      type: "bar",
      data: {
        labels: budget.labels,
        datasets: [{
          label: "Realisasi (juta Rp)",
          data: budget.values,
          backgroundColor: "#3b82f6",
          borderRadius: 6,
        }],
      },
      options: {
        responsive: true, maintainAspectRatio: false,
        plugins: { legend: { display: false } },
        scales: { y: { beginAtZero: true } },
      },
    });

    state.riskChart = new Chart($("riskChart"), {
      type: "doughnut",
      data: {
        labels: risk.labels,
        datasets: [{
          data: risk.values,
          backgroundColor: ["#22c55e", "#f59e0b", "#ef4444"],
        }],
      },
      options: { responsive: true, maintainAspectRatio: false },
    });
  }

  function clearCharts() {
    if (state.budgetChart) { state.budgetChart.destroy(); state.budgetChart = null; }
    if (state.riskChart) { state.riskChart.destroy(); state.riskChart = null; }
  }

  // ---------- Tabel ----------
  async function loadProviders() {
    var url = "/api/providers";
    if (state.currentRegion) url += "?region_code=" + encodeURIComponent(state.currentRegion);
    var data = await fetchJSON(url);
    var tbody = $("providerTable").querySelector("tbody");
    tbody.innerHTML = "";
    if (!data.length) {
      tbody.innerHTML = '<tr><td colspan="6" class="ctw-empty">Belum ada penyedia di wilayah ini.</td></tr>';
      return;
    }
    data.forEach(function (p) {
      var tr = document.createElement("tr");
      tr.innerHTML =
        "<td><strong>" + p.name + "</strong><br><small>" + (p.npwp || "-") + "</small></td>" +
        "<td>" + (p.classification || "-") + "</td>" +
        "<td>" + (p.qualification || "-") + "</td>" +
        "<td>" + (p.region || "-") + "</td>" +
        "<td><small>" + (p.contact_person || "-") + "<br>" + (p.phone || "") + "</small></td>" +
        "<td>" + (p.is_blacklisted
          ? '<span class="ctw-badge ctw-badge--blacklist">DIBLACKLIST</span>'
          : '<span class="ctw-badge ctw-badge--active">AKTIF</span>') + "</td>";
      tbody.appendChild(tr);
    });
  }

  async function loadBlacklist() {
    var data = await fetchJSON("/api/blacklist");
    var tbody = $("blacklistTable").querySelector("tbody");
    tbody.innerHTML = "";
    if (!data.length) {
      tbody.innerHTML = '<tr><td colspan="7" class="ctw-empty">Tidak ada penyedia yang di-blacklist.</td></tr>';
      return;
    }
    data.forEach(function (b) {
      var periode = (b.start_date || "-") + " s/d " + (b.end_date || "∞");
      var tr = document.createElement("tr");
      tr.innerHTML =
        "<td><strong>" + b.provider_name + "</strong></td>" +
        "<td><span class=\"ctw-badge ctw-badge--blacklist\">" + b.category + "</span></td>" +
        "<td><small>" + b.reason + "</small></td>" +
        "<td><small>" + (b.regulation_ref || "-") + "</small></td>" +
        "<td><small>" + (b.decision_number || "-") + "<br>" + (b.decision_by || "") + "</small></td>" +
        "<td><small>" + periode + "</small></td>" +
        "<td>" + b.status + "</td>";
      tbody.appendChild(tr);
    });
  }

  // ---------- Side Panel ----------
  async function openDetail(projectId) {
    $("sidePanel").classList.add("ctw-side-panel--open");
    $("panelBackdrop").classList.add("ctw-panel-backdrop--visible");
    $("panelBody").innerHTML = '<p class="ctw-empty">Memuat...</p>';
    try {
      var d = await fetchJSON("/api/projects/" + projectId + "/detail");
      renderPanel(d);
    } catch (err) {
      $("panelBody").innerHTML = '<p class="ctw-empty">Gagal memuat: ' + err.message + "</p>";
    }
  }

  function closeDetail() {
    $("sidePanel").classList.remove("ctw-side-panel--open");
    $("panelBackdrop").classList.remove("ctw-panel-backdrop--visible");
  }

  function renderPanel(d) {
    $("panelTitle").textContent = d.name;
    var regionPath = (d.region_path || []).map(function (r) { return r.name; }).join(" › ");
    var html = "";

    if (d.provider) {
      html += '<div class="ctw-panel-section"><h4>🏢 Penyedia</h4>' +
        '<p><strong>' + d.provider.name + '</strong></p>' +
        '<p class="ctw-panel-meta">' +
          (d.provider.classification || "-") + " / " + (d.provider.qualification || "-") +
          (d.provider.npwp ? "<br>NPWP: " + d.provider.npwp : "") +
          (d.provider.phone ? "<br>Telp: " + d.provider.phone : "") +
        '</p>' +
        (d.supervisor ? '<p class="ctw-panel-meta">Konsultan Pengawas: ' + d.supervisor.name + '</p>' : '') +
        '</div>';
    }

    html += '<div class="ctw-panel-section"><h4>📍 Lokasi</h4>' +
      '<p class="ctw-panel-meta">' + regionPath + '</p>' +
      (d.address ? '<p class="ctw-panel-meta">' + d.address + '</p>' : '') +
      '</div>';

    var multi = d.contract.is_multi_year ? " (Multi-Years)" : "";
    html += '<div class="ctw-panel-section"><h4>📄 Kontrak' + multi + '</h4>' +
      '<p class="ctw-panel-meta">No: ' + (d.contract.number || "-") + '</p>' +
      '<p><strong>' + formatRupiah(d.contract.value) + '</strong></p>' +
      '<p class="ctw-panel-meta">' +
        (d.contract.start || "-") + " s/d " + (d.contract.end || "-") +
        "<br>" + d.contract.duration_days + " hari kalender" +
        (d.contract.funding_source ? "<br>Sumber: " + d.contract.funding_source : "") +
        (d.contract.fiscal_year ? " (TA " + d.contract.fiscal_year + ")" : "") +
      '</p></div>';

    html += '<div class="ctw-panel-section"><h4>📊 Progres</h4>' +
      progressBar("Fisik", d.progress.physical, "#3b82f6") +
      progressBar("Keuangan", d.progress.financial, "#22c55e") +
      progressBar("Waktu", d.progress.time_work, "#f59e0b") +
      (d.progress.updated_at ? '<p class="ctw-panel-meta">Update: ' + d.progress.updated_at.slice(0, 10) + '</p>' : '') +
      '</div>';

    if (d.schedules && d.schedules.length) {
      html += '<div class="ctw-panel-section"><h4>📈 Kurva S</h4>' +
        '<div style="height:160px;"><canvas id="panelScheduleChart"></canvas></div></div>';
    }

    if (d.milestones && d.milestones.length) {
      html += '<div class="ctw-panel-section"><h4>🏁 Milestone</h4><ul class="ctw-timeline">';
      d.milestones.forEach(function (m) {
        var icon = { Done: "✅", "In Progress": "🔄", Pending: "⏳", Delayed: "⚠️" }[m.status] || "•";
        html += '<li class="ctw-timeline__item">' +
          '<span class="ctw-timeline__icon">' + icon + '</span>' +
          '<div><strong>' + m.name + '</strong>' +
          '<div class="ctw-panel-meta">' + (m.actual_date || m.target_date || "-") +
          " · " + m.progress.toFixed(0) + '%</div></div></li>';
      });
      html += "</ul></div>";
    }

    if (d.photos && d.photos.length) {
      html += '<div class="ctw-panel-section"><h4>📸 Dokumentasi</h4><div class="ctw-photo-grid">';
      d.photos.forEach(function (ph) {
        html += '<figure class="ctw-photo-item">' +
          '<img src="' + ph.url + '" alt="' + ph.caption + '" loading="lazy">' +
          '<figcaption>' + ph.caption + '</figcaption></figure>';
      });
      html += "</div></div>";
    }

    $("panelBody").innerHTML = html;

    if (d.schedules && d.schedules.length) {
      var ctx = document.getElementById("panelScheduleChart");
      if (ctx) {
        new Chart(ctx, {
          type: "line",
          data: {
            labels: d.schedules.map(function (s) { return s.period; }),
            datasets: [
              { label: "Rencana", data: d.schedules.map(function (s) { return s.planned; }),
                borderColor: "#3b82f6", backgroundColor: "rgba(59,130,246,0.1)",
                tension: 0.3, fill: true },
              { label: "Realisasi", data: d.schedules.map(function (s) { return s.actual; }),
                borderColor: "#22c55e", backgroundColor: "rgba(34,197,94,0.1)",
                tension: 0.3, fill: true },
            ],
          },
          options: {
            responsive: true, maintainAspectRatio: false,
            plugins: { legend: { position: "bottom", labels: { font: { size: 10 } } } },
            scales: { y: { beginAtZero: true, max: 100 } },
          },
        });
      }
    }
  }

  function progressBar(label, value, color) {
    var v = Math.max(0, Math.min(100, value || 0));
    return '<div class="ctw-progress">' +
      '<div class="ctw-progress__label"><span>' + label + '</span><strong>' + v.toFixed(1) + '%</strong></div>' +
      '<div class="ctw-progress__bar"><div class="ctw-progress__fill" ' +
      'style="width:' + v + '%;background:' + color + ';"></div></div></div>';
  }

  // ---------- Init ----------
  async function init() {
    initMap();
    await loadProvinces();

    var yearSel = $("filterTahun");
    var now = new Date().getFullYear();
    for (var y = now; y >= now - 5; y--) {
      var opt = document.createElement("option");
      opt.value = y;
      opt.textContent = y;
      yearSel.appendChild(opt);
    }

    $("filterProvinsi").addEventListener("change", onProvinsiChange);
    $("filterKabupaten").addEventListener("change", onKabupatenChange);
    $("filterKecamatan").addEventListener("change", onKecamatanChange);
    $("filterKelurahan").addEventListener("change", onKelurahanChange);
    $("filterTahun").addEventListener("change", function () {
      state.currentYear = this.value ? parseInt(this.value, 10) : null;
      if (state.currentRegion) loadDashboard();
    });

    var statusSel = $("filterStatus");
    if (statusSel) {
      statusSel.addEventListener("change", function () {
        state.currentStatus = this.value || "aktif";
        if (state.currentRegion) loadDashboard();
      });
    }
    $("btnReset").addEventListener("click", resetToDefault);
    $("panelClose").addEventListener("click", closeDetail);
    $("panelBackdrop").addEventListener("click", closeDetail);

    // Toggle batas wilayah
    var obsToggle = $("toggleObservations");
    if (obsToggle) {
      obsToggle.addEventListener("change", function () {
        state.showObservations = this.checked;
        if (this.checked) {
          loadObservations();
        } else {
          state.observationLayer.clearLayers();
        }
      });
    }

    $("toggleBoundaries").addEventListener("change", function () {
      state.showBoundaries = this.checked;
      if (this.checked) {
        var provCode = $("filterProvinsi").value;
        var kabCode = $("filterKabupaten").value;
        var kecCode = $("filterKecamatan").value;
        if (kecCode) loadBoundaries(kecCode, "kelurahan");
        else if (kabCode) loadBoundaries(kabCode, "kecamatan");
        else if (provCode) loadBoundaries(provCode, "kabupaten");
        else loadBoundaries(null, "provinsi");
      } else {
        state.boundaryLayer.clearLayers();
        $("boundaryInfo").textContent = "";
      }
    });

    document.addEventListener("keydown", function (e) {
      if (e.key === "Escape") closeDetail();
    });

    window.__ctwOpenDetail = openDetail;
    window.addEventListener("resize", refreshMapSize);

    // Load batas provinsi saat awal
    loadBoundaries(null, "provinsi");
    loadObservations();

    refreshMapSize();
    setTimeout(refreshMapSize, 500);
  }

  document.addEventListener("DOMContentLoaded", init);
})();
