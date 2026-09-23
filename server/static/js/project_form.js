/* CTW Project Form: cascading region + mini map + search */
(function () {
  "use strict";

  var state = {
    map: null,
    marker: null,
    selectedRegion: null,
  };

  function $(id) { return document.getElementById(id); }

  async function fetchJSON(url) {
    var res = await fetch(url);
    if (!res.ok) throw new Error("HTTP " + res.status);
    return res.json();
  }

  // ============================================================
  // CASCADING DROPDOWN
  // ============================================================

  async function loadProvinces() {
    var data = await fetchJSON("/api/regions?level=provinsi");
    var sel = $("selProvinsi");
    data.forEach(function (r) {
      var opt = document.createElement("option");
      opt.value = r.code;
      opt.textContent = r.name;
      opt.dataset.lat = r.latitude;
      opt.dataset.lng = r.longitude;
      sel.appendChild(opt);
    });
  }

  async function loadChildren(level, parentCode, targetId, placeholder) {
    var sel = $(targetId);
    sel.innerHTML = '<option value="">— ' + placeholder + ' —</option>';
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

  function resetRegionField(id, placeholder) {
    var el = $(id);
    el.innerHTML = '<option value="">— ' + placeholder + ' —</option>';
    el.disabled = true;
  }

  async function onProvinsiChange() {
    resetRegionField("selKabupaten", "Pilih Kabupaten/Kota");
    resetRegionField("selKecamatan", "Pilih Kecamatan");
    resetRegionField("selKelurahan", "Pilih Kelurahan/Desa");
    var code = $("selProvinsi").value;
    if (code) {
      await loadChildren("kabupaten", code, "selKabupaten", "Pilih Kabupaten/Kota");
      setRegionCode(code);
    } else {
      clearRegionCode();
    }
  }

  async function onKabupatenChange() {
    resetRegionField("selKecamatan", "Pilih Kecamatan");
    resetRegionField("selKelurahan", "Pilih Kelurahan/Desa");
    var code = $("selKabupaten").value;
    if (code) {
      await loadChildren("kecamatan", code, "selKecamatan", "Pilih Kecamatan");
      setRegionCode(code);
    } else {
      setRegionCode($("selProvinsi").value);
    }
  }

  async function onKecamatanChange() {
    resetRegionField("selKelurahan", "Pilih Kelurahan/Desa");
    var code = $("selKecamatan").value;
    if (code) {
      await loadChildren("kelurahan", code, "selKelurahan", "Pilih Kelurahan/Desa");
      setRegionCode(code);
    } else {
      setRegionCode($("selKabupaten").value);
    }
  }

  function onKelurahanChange() {
    var code = $("selKelurahan").value;
    if (code) {
      setRegionCode(code);
    } else {
      setRegionCode($("selKecamatan").value);
    }
  }

  function setRegionCode(code) {
    $("region_code").value = code || "";
    updateRegionPathInfo();
    if (code) {
      // Auto-fill koordinat dari wilayah terpilih
      var opt = findSelectedOption(code);
      if (opt && opt.dataset.lat && opt.dataset.lng) {
        var lat = parseFloat(opt.dataset.lat);
        var lng = parseFloat(opt.dataset.lng);
        if (!isNaN(lat) && !isNaN(lng)) {
          // Auto-isi kalau kosong
          if (!$("latitude").value) $("latitude").value = lat.toFixed(6);
          if (!$("longitude").value) $("longitude").value = lng.toFixed(6);
          // Update map
          setMapLocation(lat, lng, true);
        }
      }
    }
  }

  function findSelectedOption(code) {
    var selects = ["selProvinsi", "selKabupaten", "selKecamatan", "selKelurahan"];
    for (var i = 0; i < selects.length; i++) {
      var opt = $(selects[i]).querySelector('option[value="' + code + '"]');
      if (opt) return opt;
    }
    return null;
  }

  function clearRegionCode() {
    $("region_code").value = "";
    $("regionPathInfo").style.display = "none";
  }

  async function updateRegionPathInfo() {
    var code = $("region_code").value;
    if (!code) {
      $("regionPathInfo").style.display = "none";
      return;
    }
    try {
      var data = await fetchJSON("/api/regions/" + code + "/path");
      var path = data.path.map(function (p) { return p.name; }).join(" › ");
      $("regionPathText").textContent = path;
      $("regionPathInfo").style.display = "block";
    } catch (e) {
      $("regionPathInfo").style.display = "none";
    }
  }

  // ============================================================
  // SEARCH REGION
  // ============================================================

  var searchTimer = null;

  function onSearchInput() {
    clearTimeout(searchTimer);
    var q = $("regionSearch").value.trim();
    var results = $("regionSearchResults");

    if (q.length < 2) {
      results.style.display = "none";
      return;
    }

    searchTimer = setTimeout(async function () {
      try {
        var data = await fetchJSON("/api/regions/search?q=" + encodeURIComponent(q));
        renderSearchResults(data);
      } catch (e) {
        console.error(e);
      }
    }, 250);
  }

  function renderSearchResults(items) {
    var box = $("regionSearchResults");
    if (!items.length) {
      box.innerHTML = '<div class="region-search-empty">Tidak ada hasil untuk pencarian ini</div>';
      box.style.display = "block";
      return;
    }
    var html = "";
    items.forEach(function (r) {
      var levelLabel = ({ provinsi: "Provinsi", kabupaten: "Kabupaten/Kota",
                          kecamatan: "Kecamatan", kelurahan: "Kelurahan/Desa" })[r.level] || r.level;
      html += '<div class="region-search-item" data-code="' + r.code + '" data-level="' + r.level + '">' +
                '<div><strong>' + r.name + '</strong></div>' +
                '<div class="region-search-item__meta">' + levelLabel + ' · ' + r.code + '</div>' +
              '</div>';
    });
    box.innerHTML = html;
    box.style.display = "block";

    box.querySelectorAll(".region-search-item").forEach(function (el) {
      el.addEventListener("click", function () {
        applySearchResult(el.dataset.code, el.dataset.level);
      });
    });
  }

  async function applySearchResult(code, level) {
    $("regionSearchResults").style.display = "none";
    $("regionSearch").value = "";

    // Muat path lengkap untuk tahu parent-nya
    try {
      var data = await fetchJSON("/api/regions/" + code + "/path");
      var path = data.path;  // [{code, name, level}, ...] top-down

      // Populasi dropdown sesuai path
      for (var i = 0; i < path.length; i++) {
        var node = path[i];
        var targetSel, placeholder;
        if (node.level === "provinsi") { targetSel = "selProvinsi"; placeholder = "Pilih Provinsi"; }
        else if (node.level === "kabupaten") { targetSel = "selKabupaten"; placeholder = "Pilih Kabupaten/Kota"; }
        else if (node.level === "kecamatan") { targetSel = "selKecamatan"; placeholder = "Pilih Kecamatan"; }
        else if (node.level === "kelurahan") { targetSel = "selKelurahan"; placeholder = "Pilih Kelurahan/Desa"; }
        else continue;

        var sel = $(targetSel);
        // Load children dulu
        if (node.level !== "provinsi") {
          var parentNode = path[i - 1];
          var childLevel = node.level;
          var parentSelId = { kabupaten: "selProvinsi", kecamatan: "selKabupaten", kelurahan: "selKecamatan" }[node.level];
          await loadChildren(childLevel, parentNode.code, targetSel, placeholder);
        }
        // Set value
        sel.value = node.code;
      }
      // Update hidden + info
      setRegionCode(code);
    } catch (e) {
      console.error(e);
      if (window.CTW && window.CTW.toast) window.CTW.toast.error("Gagal load wilayah");
    }
  }

  // Close search dropdown kalau klik di luar
  document.addEventListener("click", function (e) {
    if (!e.target.closest(".region-search-wrap")) {
      $("regionSearchResults").style.display = "none";
    }
  });

  // ============================================================
  // MINI MAP
  // ============================================================

  function initMiniMap() {
    var lat = parseFloat($("latitude").value) || -2.5489;
    var lng = parseFloat($("longitude").value) || 118.0149;
    var zoom = $("latitude").value ? 13 : 5;

    state.map = L.map("miniMap", {
      center: [lat, lng],
      zoom: zoom,
      scrollWheelZoom: true,
    });

    L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
      attribution: "&copy; OpenStreetMap",
      maxZoom: 19,
    }).addTo(state.map);

    // Marker draggable (kalau ada lat/lng, tampilkan; kalau tidak, biarkan kosong)
    if ($("latitude").value && $("longitude").value) {
      createMarker(lat, lng);
    }

    // Klik peta → pindah marker atau buat baru
    state.map.on("click", function (e) {
      var newLat = e.latlng.lat;
      var newLng = e.latlng.lng;
      $("latitude").value = newLat.toFixed(6);
      $("longitude").value = newLng.toFixed(6);
      if (state.marker) {
        state.marker.setLatLng([newLat, newLng]);
      } else {
        createMarker(newLat, newLng);
      }
      if (window.CTW && window.CTW.toast) {
        window.CTW.toast.success("Koordinat diperbarui", 1500);
      }
    });

    // Fix size
    setTimeout(function () { state.map.invalidateSize(); }, 200);
  }

  function createMarker(lat, lng) {
    state.marker = L.marker([lat, lng], {
      draggable: true,
      autoPan: true,
    }).addTo(state.map);

    state.marker.bindPopup("📍 Lokasi proyek<br><small>Geser marker untuk menyesuaikan</small>").openPopup();

    state.marker.on("dragend", function () {
      var pos = state.marker.getLatLng();
      $("latitude").value = pos.lat.toFixed(6);
      $("longitude").value = pos.lng.toFixed(6);
    });
  }

  function setMapLocation(lat, lng, moveMap) {
    if (!state.map) return;
    if (!state.marker) {
      createMarker(lat, lng);
    } else {
      state.marker.setLatLng([lat, lng]);
    }
    if (moveMap) {
      state.map.setView([lat, lng], Math.max(state.map.getZoom(), 13));
    }
  }

  // ============================================================
  // EVENT LISTENERS
  // ============================================================

  function bindEvents() {
    $("selProvinsi").addEventListener("change", onProvinsiChange);
    $("selKabupaten").addEventListener("change", onKabupatenChange);
    $("selKecamatan").addEventListener("change", onKecamatanChange);
    $("selKelurahan").addEventListener("change", onKelurahanChange);

    $("regionSearch").addEventListener("input", onSearchInput);

    $("btnUseRegionCoord").addEventListener("click", function () {
      var code = $("region_code").value;
      if (!code) {
        if (window.CTW) window.CTW.toast.warning("Pilih wilayah dulu di atas");
        return;
      }
      var opt = findSelectedOption(code);
      if (!opt || !opt.dataset.lat || !opt.dataset.lng) {
        if (window.CTW) window.CTW.toast.warning("Koordinat wilayah tidak tersedia");
        return;
      }
      var lat = parseFloat(opt.dataset.lat);
      var lng = parseFloat(opt.dataset.lng);
      $("latitude").value = lat.toFixed(6);
      $("longitude").value = lng.toFixed(6);
      setMapLocation(lat, lng, true);
      if (window.CTW) window.CTW.toast.success("Koordinat diisi dari wilayah terpilih");
    });

    $("btnLocateMap").addEventListener("click", function () {
      var lat = parseFloat($("latitude").value);
      var lng = parseFloat($("longitude").value);
      if (isNaN(lat) || isNaN(lng)) {
        if (window.CTW) window.CTW.toast.warning("Isi latitude & longitude dulu");
        return;
      }
      setMapLocation(lat, lng, true);
    });

    // Sync map saat lat/lng manual diubah
    $("latitude").addEventListener("change", updateMapFromInputs);
    $("longitude").addEventListener("change", updateMapFromInputs);
  }

  function updateMapFromInputs() {
    var lat = parseFloat($("latitude").value);
    var lng = parseFloat($("longitude").value);
    if (!isNaN(lat) && !isNaN(lng)) {
      setMapLocation(lat, lng, false);
    }
  }

  // ============================================================
  // PRE-SELECT (untuk mode edit)
  // ============================================================

  async function preloadExistingRegion() {
    var el = document.getElementById("preload-region");
    if (!el) return;
    var preload;
    try {
      preload = JSON.parse(el.textContent);
    } catch (e) {
      return;
    }
    if (!preload || !preload.code) return;
    // Gunakan path seperti search
    await applySearchResult(preload.code, null);
  }

  // ============================================================
  // INIT
  // ============================================================

  async function init() {
    await loadProvinces();
    initMiniMap();
    bindEvents();
    await preloadExistingRegion();
  }

  document.addEventListener("DOMContentLoaded", init);
})();
