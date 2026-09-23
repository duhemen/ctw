/* CTW UI Utilities - Toast, Skeleton, Loading */
(function (global) {
  "use strict";

  // ============ TOAST ============
  var toastContainer = null;

  function ensureContainer() {
    if (toastContainer) return;
    toastContainer = document.createElement("div");
    toastContainer.className = "ctw-toast-container";
    document.body.appendChild(toastContainer);
  }

  function showToast(message, type, duration) {
    type = type || "info";
    duration = duration || 4000;

    ensureContainer();

    var icons = {
      success: "\u2705",
      error: "\u26A0\uFE0F",
      info: "\u2139\uFE0F",
      warning: "\uD83D\uDD14",
    };

    var el = document.createElement("div");
    el.className = "ctw-toast ctw-toast--" + type;
    el.innerHTML =
      '<span class="ctw-toast__icon">' + (icons[type] || "") + "</span>" +
      '<span class="ctw-toast__message">' + message + "</span>" +
      '<button class="ctw-toast__close" aria-label="Tutup">&times;</button>';

    toastContainer.appendChild(el);

    // Trigger animasi masuk
    requestAnimationFrame(function () {
      el.classList.add("ctw-toast--in");
    });

    var closeBtn = el.querySelector(".ctw-toast__close");
    function close() {
      el.classList.remove("ctw-toast--in");
      el.classList.add("ctw-toast--out");
      setTimeout(function () {
        if (el.parentNode) el.parentNode.removeChild(el);
      }, 300);
    }
    closeBtn.addEventListener("click", close);

    if (duration > 0) {
      setTimeout(close, duration);
    }
  }

  var toast = {
    success: function (msg, dur) { showToast(msg, "success", dur); },
    error: function (msg, dur) { showToast(msg, "error", dur); },
    info: function (msg, dur) { showToast(msg, "info", dur); },
    warning: function (msg, dur) { showToast(msg, "warning", dur); },
  };

  // ============ AUTO-TOAST dari URL params ============
  function autoToastFromUrl() {
    var params = new URLSearchParams(window.location.search);
    var success = params.get("success");
    var error = params.get("error");

    if (success) {
      var msgs = {
        created: "Data berhasil dibuat",
        updated: "Perubahan berhasil disimpan",
        deleted: "Data berhasil dihapus",
        uploaded: "File berhasil diunggah",
        "1": "Terima kasih! Laporan Anda telah diterima.",
      };
      toast.success(msgs[success] || "Berhasil");
    }

    if (error) {
      toast.error(decodeURIComponent(error));
    }
  }

  // ============ SCROLL TO TOP ============
  function initScrollTop() {
    var btn = document.createElement("button");
    btn.className = "ctw-scroll-top";
    btn.innerHTML = "\u2191";
    btn.setAttribute("aria-label", "Kembali ke atas");
    btn.addEventListener("click", function () {
      window.scrollTo({ top: 0, behavior: "smooth" });
    });
    document.body.appendChild(btn);

    window.addEventListener("scroll", function () {
      if (window.scrollY > 400) {
        btn.classList.add("ctw-scroll-top--visible");
      } else {
        btn.classList.remove("ctw-scroll-top--visible");
      }
    });
  }

  // ============ COPY TO CLIPBOARD ============
  function copyToClipboard(text, successMsg) {
    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(text).then(function () {
        toast.success(successMsg || "Tersalin ke clipboard");
      }).catch(function () {
        toast.error("Gagal menyalin");
      });
    } else {
      // Fallback
      var ta = document.createElement("textarea");
      ta.value = text;
      document.body.appendChild(ta);
      ta.select();
      try {
        document.execCommand("copy");
        toast.success(successMsg || "Tersalin");
      } catch (e) {
        toast.error("Gagal menyalin");
      }
      document.body.removeChild(ta);
    }
  }

  // ============ SKELETON HELPERS ============
  function showSkeleton(el, count) {
    count = count || 3;
    if (!el) return;
    var html = "";
    for (var i = 0; i < count; i++) {
      html += '<div class="ctw-skeleton ctw-skeleton--row"></div>';
    }
    el.innerHTML = html;
  }

  // ============ KEYBOARD SHORTCUTS ============
  function initKeyboard() {
    document.addEventListener("keydown", function (e) {
      // Esc: tutup panel/modal
      if (e.key === "Escape") {
        var panel = document.getElementById("sidePanel");
        if (panel && panel.classList.contains("ctw-side-panel--open")) {
          panel.classList.remove("ctw-side-panel--open");
          var bd = document.getElementById("panelBackdrop");
          if (bd) bd.classList.remove("ctw-panel-backdrop--visible");
        }
      }
      // "/" fokus ke search (kalau ada)
      if (e.key === "/" && !["INPUT", "TEXTAREA", "SELECT"].includes(document.activeElement.tagName)) {
        var search = document.getElementById("globalSearch");
        if (search) {
          e.preventDefault();
          search.focus();
        }
      }
    });
  }

  // ============ FADE-IN ON SCROLL ============
  function initScrollReveal() {
    if (!("IntersectionObserver" in window)) return;
    var observer = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (entry.isIntersecting) {
          entry.target.classList.add("ctw-reveal--visible");
          observer.unobserve(entry.target);
        }
      });
    }, { threshold: 0.1, rootMargin: "0px 0px -50px 0px" });

    document.querySelectorAll(".ctw-reveal").forEach(function (el) {
      observer.observe(el);
    });
  }

  // ============ INIT ============
  function init() {
    autoToastFromUrl();
    initScrollTop();
    initKeyboard();
    initScrollReveal();

    // Auto-hide alert lama (kalau ada)
    document.querySelectorAll(".ctw-alert, .admin-alert").forEach(function (el) {
      setTimeout(function () {
        el.style.transition = "opacity 0.5s, transform 0.5s";
        el.style.opacity = "0";
        el.style.transform = "translateY(-10px)";
        setTimeout(function () { el.style.display = "none"; }, 500);
      }, 5000);
    });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }

  // Expose global
  global.CTW = global.CTW || {};
  global.CTW.toast = toast;
  global.CTW.copy = copyToClipboard;
  global.CTW.skeleton = showSkeleton;
})(window);
