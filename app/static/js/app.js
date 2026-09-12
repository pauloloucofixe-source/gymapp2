/* GymTracker – camada de interatividade iOS-style */
(function () {
  "use strict";

  /* ---------- Haptics ---------- */
  function haptic(pattern) {
    if (navigator.vibrate) navigator.vibrate(pattern || 8);
  }

  /* ---------- Toasts ---------- */
  const ICONS = {
    success: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M20 6 9 17l-5-5"/></svg>',
    error: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>'
  };

  function toast(message, type) {
    type = type || "success";
    const container = document.getElementById("toast-container");
    if (!container) return;
    const el = document.createElement("div");
    el.className = "toast " + type;
    el.innerHTML = (ICONS[type] || "") + "<span>" + message + "</span>";
    container.appendChild(el);
    requestAnimationFrame(() => el.classList.add("show"));
    haptic(type === "error" ? [10, 30, 10] : 8);
    setTimeout(() => {
      el.classList.remove("show");
      setTimeout(() => el.remove(), 300);
    }, 2600);
  }
  window.iosToast = toast;

  /* ---------- Bottom sheets ---------- */
  function openSheet(id) {
    const overlay = document.getElementById(id);
    if (!overlay) return;
    overlay.classList.add("open");
    haptic(6);
    const firstInput = overlay.querySelector("input, select, textarea");
    if (firstInput) setTimeout(() => firstInput.focus({ preventScroll: true }), 300);
  }

  function closeSheet(id) {
    const overlay = typeof id === "string" ? document.getElementById(id) : id;
    if (!overlay) return;
    overlay.classList.remove("open");
  }

  window.iosSheet = { open: openSheet, close: closeSheet };

  document.addEventListener("click", (e) => {
    const opener = e.target.closest("[data-sheet-open]");
    if (opener) {
      openSheet(opener.getAttribute("data-sheet-open"));
      return;
    }
    const closer = e.target.closest("[data-sheet-close]");
    if (closer) {
      closeSheet(closer.closest(".sheet-overlay"));
      return;
    }
    if (e.target.classList && e.target.classList.contains("sheet-overlay")) {
      closeSheet(e.target);
    }
  });

  /* ---------- Stagger entrance for cards / list items ---------- */
  function applyStagger(root) {
    (root || document).querySelectorAll(".ios-card, .swipe-wrap").forEach((el, i) => {
      el.style.setProperty("--i", Math.min(i, 8));
    });
  }
  applyStagger(document);

  /* ---------- Button loading state ---------- */
  function setLoading(btn, loading) {
    if (!btn) return;
    if (loading) {
      btn.classList.add("loading");
      btn.disabled = true;
    } else {
      btn.classList.remove("loading");
      btn.disabled = false;
    }
  }

  /* ---------- AJAX forms ----------
     Forms with [data-ajax] submit via fetch instead of a full page reload.
     On success, the server returns JSON. A callback registered via
     data-ajax-success="fnName" (a global function name) receives the JSON. */
  document.addEventListener("submit", async function (e) {
    const form = e.target;
    if (!form.matches("[data-ajax]")) return;
    e.preventDefault();

    const btn = form.querySelector('button[type="submit"]');
    setLoading(btn, true);

    try {
      const res = await fetch(form.action || window.location.href, {
        method: form.method || "POST",
        headers: { "X-Requested-With": "fetch" },
        body: new FormData(form)
      });

      if (!res.ok) throw new Error("Request failed");
      const data = await res.json();

      const cb = form.getAttribute("data-ajax-success");
      if (cb && typeof window[cb] === "function") {
        window[cb](data, form);
      }

      if (!form.hasAttribute("data-no-reset")) {
        form.reset();
        const dateInput = form.querySelector('input[type="date"]');
        if (dateInput && dateInput.dataset.today) dateInput.value = dateInput.dataset.today;
      }

      if (!form.hasAttribute("data-keep-sheet-open")) {
        const sheet = form.closest(".sheet-overlay");
        if (sheet) closeSheet(sheet);
      } else {
        haptic(8);
      }

      toast(form.getAttribute("data-success-message") || "Guardado com sucesso", "success");
    } catch (err) {
      toast("Não foi possível guardar. Tenta novamente.", "error");
    } finally {
      setLoading(btn, false);
    }
  });

  /* ---------- Swipe to delete ----------
     Structure expected:
     <li class="swipe-wrap">
       <div class="swipe-actions"><button class="swipe-delete-btn" data-delete-url="...">Apagar</button></div>
       <div class="swipe-content">...visible row...</div>
     </li> */
  const REVEAL = 84;

  function initSwipe(root) {
    (root || document).querySelectorAll(".swipe-wrap").forEach((wrap) => {
      if (wrap.dataset.swipeInit) return;
      wrap.dataset.swipeInit = "1";

      const content = wrap.querySelector(".swipe-content");
      const delBtn = wrap.querySelector(".swipe-delete-btn");
      if (!content) return;

      let startX = 0, currentX = 0, dragging = false;

      content.addEventListener("touchstart", (e) => {
        startX = e.touches[0].clientX;
        dragging = true;
        content.style.transition = "none";
      }, { passive: true });

      content.addEventListener("touchmove", (e) => {
        if (!dragging) return;
        const dx = e.touches[0].clientX - startX;
        currentX = Math.min(0, Math.max(dx, -REVEAL - 20));
        content.style.transform = `translateX(${currentX}px)`;
      }, { passive: true });

      content.addEventListener("touchend", () => {
        dragging = false;
        content.style.transition = "";
        if (currentX < -REVEAL / 2) {
          content.style.transform = `translateX(-${REVEAL}px)`;
          haptic(10);
        } else {
          content.style.transform = "translateX(0)";
        }
      });

      // Tap elsewhere closes an open swipe row
      document.addEventListener("click", (e) => {
        if (!wrap.contains(e.target)) {
          content.style.transform = "translateX(0)";
        }
      });

      if (delBtn) {
        delBtn.addEventListener("click", async () => {
          const url = delBtn.getAttribute("data-delete-url");
          if (!url) return;
          haptic([10, 30, 10]);
          try {
            const res = await fetch(url, {
              method: "DELETE",
              headers: { "X-Requested-With": "fetch" }
            });
            if (!res.ok) throw new Error("delete failed");
            content.classList.add("removing");
            content.style.transform = "translateX(-100%)";
            wrap.style.maxHeight = wrap.offsetHeight + "px";
            requestAnimationFrame(() => { wrap.style.maxHeight = "0px"; wrap.style.overflow = "hidden"; });
            setTimeout(() => {
              wrap.remove();
              maybeShowEmptyState(wrap);
            }, 320);
            toast("Removido", "success");
          } catch (err) {
            toast("Não foi possível remover.", "error");
            content.style.transform = "translateX(0)";
          }
        });
      }
    });
  }

  function maybeShowEmptyState(removedWrap) {
    const list = removedWrap.closest ? null : null; // placeholder (list lookup done per-page if needed)
  }

  initSwipe(document);

  /* One-tap POST helper (for quick actions outside a <form>, e.g. "repetir última série") */
  async function postForm(url, data) {
    const body = new URLSearchParams(data);
    const res = await fetch(url, {
      method: "POST",
      headers: {
        "X-Requested-With": "fetch",
        "Content-Type": "application/x-www-form-urlencoded"
      },
      body
    });
    if (!res.ok) throw new Error("request failed");
    return res.json();
  }

  /* Expose for pages that inject new list items dynamically */
  window.iosInteractive = {
    applyStagger,
    initSwipe,
    toast,
    postForm,
    haptic
  };
})();
