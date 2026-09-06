(function () {
  "use strict";

  var STORAGE_KEY = "quoteItems";

  /* ------------------------------------------------------------------ */
  /* ユーティリティ                                                      */
  /* ------------------------------------------------------------------ */
  function yen(n) {
    return "¥" + Number(n || 0).toLocaleString("ja-JP");
  }

  function getQuoteItems() {
    try {
      var raw = window.localStorage.getItem(STORAGE_KEY);
      return raw ? JSON.parse(raw) : [];
    } catch (e) {
      return [];
    }
  }

  function saveQuoteItems(items) {
    try {
      window.localStorage.setItem(STORAGE_KEY, JSON.stringify(items));
    } catch (e) {
      /* localStorageが使えない環境は静かに諦める */
    }
    updateHeaderCount();
  }

  function updateHeaderCount() {
    var el = document.getElementById("quote-count");
    if (!el) return;
    var items = getQuoteItems();
    el.textContent = String(items.length);
  }

  /* ------------------------------------------------------------------ */
  /* ヘッダー：モバイルナビ開閉                                          */
  /* ------------------------------------------------------------------ */
  function initNavToggle() {
    var btn = document.getElementById("nav-toggle");
    var nav = document.getElementById("site-nav");
    if (!btn || !nav) return;
    btn.addEventListener("click", function () {
      var isOpen = nav.classList.toggle("is-open");
      btn.setAttribute("aria-expanded", isOpen ? "true" : "false");
    });
  }

  /* ------------------------------------------------------------------ */
  /* 「見積もりに追加」ボタン（トップページ・商品一覧ページ共通）           */
  /* ------------------------------------------------------------------ */
  function markAddedButtons() {
    var items = getQuoteItems();
    var ids = items.map(function (it) { return String(it.id); });
    document.querySelectorAll("[data-add-to-quote]").forEach(function (btn) {
      if (ids.indexOf(String(btn.dataset.id)) !== -1) {
        btn.classList.add("is-added");
        btn.textContent = "追加済み（見積もりへ）";
      } else {
        btn.classList.remove("is-added");
        btn.textContent = "見積もりに追加";
      }
    });
  }

  function initAddToQuoteButtons(quoteModal) {
    document.addEventListener("click", function (e) {
      var btn = e.target.closest("[data-add-to-quote]");
      if (!btn) return;

      var id = String(btn.dataset.id);
      var items = getQuoteItems();
      var idx = items.findIndex(function (it) { return String(it.id) === id; });
      var addedItem = null;

      if (idx === -1) {
        addedItem = {
          id: id,
          name: btn.dataset.name,
          model: btn.dataset.model,
          image: btn.dataset.image,
          price: Number(btn.dataset.price) || 0,
          qty: 1
        };
        items.push(addedItem);
      } else {
        items.splice(idx, 1);
      }

      saveQuoteItems(items);
      markAddedButtons();

      if (addedItem && quoteModal) {
        quoteModal.open(addedItem);
      }
    });
  }

  /* ------------------------------------------------------------------ */
  /* 「見積もりに追加しました」ポップアップ                                */
  /* ------------------------------------------------------------------ */
  function initQuoteAddedModal() {
    var modal = document.getElementById("quote-added-modal");
    if (!modal) return null;

    var photoEl = document.getElementById("quote-modal-photo");
    var nameEl = document.getElementById("quote-modal-name");

    function open(item) {
      if (photoEl) {
        photoEl.src = item.image || "";
        photoEl.alt = item.name || "";
      }
      if (nameEl) nameEl.textContent = item.name || "";
      modal.hidden = false;
    }

    function close() {
      modal.hidden = true;
    }

    modal.querySelectorAll("[data-modal-close]").forEach(function (el) {
      el.addEventListener("click", close);
    });

    document.addEventListener("keydown", function (e) {
      if (e.key === "Escape" && !modal.hidden) close();
    });

    return { open: open, close: close };
  }

  /* ------------------------------------------------------------------ */
  /* 商品一覧ページ：カテゴリー絞り込み・検索                             */
  /* ------------------------------------------------------------------ */
  function initProductBrowser() {
    var grid = document.getElementById("product-grid");
    if (!grid) return;

    var searchInput = document.getElementById("product-search");
    var chips = document.querySelectorAll("#category-chips .chip");
    var items = Array.prototype.slice.call(grid.querySelectorAll(".browser__item"));
    var resultCount = document.getElementById("result-count");
    var emptyState = document.getElementById("empty-state");

    var params = new URLSearchParams(window.location.search);
    var initialCategory = params.get("category") || "ALL";

    var activeCategory = "ALL";
    chips.forEach(function (chip) {
      if (chip.dataset.filter === initialCategory) {
        activeCategory = initialCategory;
      }
    });

    function applyFilter() {
      var keyword = (searchInput.value || "").trim().toLowerCase();
      var visible = 0;

      items.forEach(function (item) {
        var matchesCategory = activeCategory === "ALL" || item.dataset.major === activeCategory;
        var matchesKeyword = !keyword || item.dataset.keyword.indexOf(keyword) !== -1;
        var show = matchesCategory && matchesKeyword;
        item.classList.toggle("is-hidden", !show);
        if (show) visible += 1;
      });

      resultCount.textContent = visible + "件を表示中";
      emptyState.hidden = visible !== 0;
    }

    chips.forEach(function (chip) {
      chip.classList.toggle("is-active", chip.dataset.filter === activeCategory);
      chip.addEventListener("click", function () {
        activeCategory = chip.dataset.filter;
        chips.forEach(function (c) { c.classList.toggle("is-active", c === chip); });
        applyFilter();
      });
    });

    searchInput.addEventListener("input", applyFilter);

    applyFilter();
  }

  /* ------------------------------------------------------------------ */
  /* 見積もりリストページ                                                */
  /* ------------------------------------------------------------------ */
  function renderQuoteRow(item) {
    var row = document.createElement("div");
    row.className = "quote-row";
    row.dataset.id = item.id;
    row.innerHTML =
      '<span class="quote-row__photo"><img src="' + item.image + '" alt=""></span>' +
      '<span class="quote-row__info">' +
        '<span class="quote-row__name">' + item.name + '</span>' +
        '<span class="quote-row__model mono">型番 ' + item.model + '</span>' +
      '</span>' +
      '<span class="quote-row__qty">' +
        '<input type="number" min="1" value="' + (item.qty || 1) + '" aria-label="数量">' +
      '</span>' +
      '<span class="quote-row__price-col">' +
        '<span class="quote-row__price mono">' + yen(item.price * (item.qty || 1)) + '</span>' +
        '<button type="button" class="quote-row__remove">削除</button>' +
      '</span>';
    return row;
  }

  function initQuotePage() {
    var listEl = document.getElementById("quote-list");
    if (!listEl) return;

    var emptyEl = document.getElementById("quote-empty");
    var formWrap = document.getElementById("quote-form-wrap");
    var totalEl = document.getElementById("quote-total");

    function render() {
      var items = getQuoteItems();
      listEl.innerHTML = "";

      if (items.length === 0) {
        emptyEl.hidden = false;
        formWrap.hidden = true;
        return;
      }

      emptyEl.hidden = true;
      formWrap.hidden = false;

      var total = 0;
      items.forEach(function (item) {
        total += item.price * (item.qty || 1);
        listEl.appendChild(renderQuoteRow(item));
      });
      totalEl.textContent = yen(total);
    }

    listEl.addEventListener("click", function (e) {
      var btn = e.target.closest(".quote-row__remove");
      if (!btn) return;
      var row = btn.closest(".quote-row");
      var id = row.dataset.id;
      var items = getQuoteItems().filter(function (it) { return String(it.id) !== String(id); });
      saveQuoteItems(items);
      render();
    });

    listEl.addEventListener("change", function (e) {
      if (e.target.type !== "number") return;
      var row = e.target.closest(".quote-row");
      var id = row.dataset.id;
      var qty = Math.max(1, parseInt(e.target.value, 10) || 1);
      var items = getQuoteItems();
      var target = items.find(function (it) { return String(it.id) === String(id); });
      if (target) target.qty = qty;
      saveQuoteItems(items);
      render();
    });

    var form = document.getElementById("quote-request-form");
    var itemsField = document.getElementById("quote-items-field");
    if (form && itemsField) {
      form.addEventListener("submit", function () {
        var items = getQuoteItems();

        var lines = [];
        var total = 0;
        items.forEach(function (item) {
          var lineTotal = item.price * (item.qty || 1);
          total += lineTotal;
          lines.push(
            "・" + item.name + "（型番:" + item.model + "） 数量" + (item.qty || 1) +
            " 参考価格" + yen(item.price) + " 小計" + yen(lineTotal)
          );
        });
        lines.push("");
        lines.push("参考合計（税込）：" + yen(total));

        itemsField.value = lines.join("\n");
      });
    }

    render();
  }

  /* ------------------------------------------------------------------ */
  /* init                                                                */
  /* ------------------------------------------------------------------ */
  document.addEventListener("DOMContentLoaded", function () {
    initNavToggle();
    var quoteModal = initQuoteAddedModal();
    initAddToQuoteButtons(quoteModal);
    markAddedButtons();
    updateHeaderCount();
    initProductBrowser();
    initQuotePage();
  });
})();
