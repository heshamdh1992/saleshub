(function () {
    function getMode() {
        return window.POS_MODE || "offline";
    }

    function updateSyncStatusBadge(message = "", variant = "success") {
        const badge = document.getElementById("sync-status-badge");
        if (!badge) return;

        if (!message) {
            badge.classList.add("d-none");
            badge.textContent = "";
            badge.classList.remove("bg-success", "bg-danger", "bg-warning", "bg-info", "text-dark");
            return;
        }

        badge.classList.remove("d-none", "bg-success", "bg-danger", "bg-warning", "bg-info", "text-dark");

        if (variant === "danger") {
            badge.classList.add("bg-danger");
        } else if (variant === "warning") {
            badge.classList.add("bg-warning", "text-dark");
        } else if (variant === "info") {
            badge.classList.add("bg-info");
        } else {
            badge.classList.add("bg-success");
        }

        badge.textContent = message;
    }

    async function updateOfflineQueueBadge() {
        const badge = document.getElementById("offline-queue-badge");
        if (!badge || typeof getOfflineQueueSummary !== "function") return;

        try {
            const summary = await getOfflineQueueSummary();

            const pending = Number(summary.pending_sales_count || 0);
            const syncing = Number(summary.syncing_sales_count || 0);
            const failed = Number(summary.failed_sales_count || 0);
            const blocked = Number(summary.blocked_sales_count || 0);

            if (pending === 0 && syncing === 0 && failed === 0 && blocked === 0) {
                badge.classList.add("d-none");
                badge.textContent = "";
                badge.classList.remove("bg-danger", "bg-warning", "bg-info", "bg-dark", "text-dark");
                return;
            }

            badge.classList.remove("d-none", "bg-danger", "bg-warning", "bg-info", "bg-dark", "text-dark");

            if (blocked > 0) {
                badge.classList.add("bg-dark");
                badge.textContent = `محجوب: ${blocked}`;
                return;
            }

            if (failed > 0) {
                badge.classList.add("bg-danger");
                badge.textContent = `فشل: ${failed}`;
                return;
            }

            if (syncing > 0) {
                badge.classList.add("bg-info");
                badge.textContent = `مزامنة: ${syncing}`;
                return;
            }

            badge.classList.add("bg-warning", "text-dark");
            badge.textContent = `معلّق: ${pending}`;
        } catch (error) {
            console.error(error);
        }
    }

    function renderProducts(products) {
        const container = document.getElementById("offline-products-container");
        if (!container) return;

        if (!products || !products.length) {
            container.innerHTML = `
                <div class="list-group-item text-center text-muted">
                    لا توجد منتجات
                </div>
            `;
            return;
        }

        container.innerHTML = products.map(product => `
            <div class="list-group-item py-3">
                <div class="d-flex justify-content-between align-items-center gap-2">
                    <div class="flex-grow-1">
                        <div class="fw-bold">${product.name || "بدون اسم"}</div>
                        <small class="text-muted d-block">${product.barcode || "-"}</small>
                        <small class="text-muted d-block">المخزون: ${product.stock_quantity ?? 0}</small>
                    </div>

                    <div class="text-start">
                        <div class="fw-bold mb-2">$${Number(product.base_price_usd || 0).toFixed(2)}</div>
                        <button
                            type="button"
                            class="btn btn-sm btn-dark offline-add-to-cart-btn"
                            data-product-id="${product.id}"
                            ${Number(product.stock_quantity || 0) <= 0 ? "disabled" : ""}
                        >
                            ${Number(product.stock_quantity || 0) <= 0 ? "نفد" : "إضافة"}
                        </button>
                    </div>
                </div>
            </div>
        `).join("");
    }

    async function handleAddToCart(button) {
        const id = Number(button.dataset.productId || 0);
        if (!id) return;

        try {
            const products = await searchOfflineProducts("");
            const product = products.find(p => Number(p.id) === id);

            if (!product) {
                showAppToast("المنتج غير موجود محليًا.", "warning");
                return;
            }

            await addOfflineProductToCart(product);
            await refreshOfflineCartUI();
            showAppToast("تمت إضافة المنتج إلى السلة.", "success", 1200);
        } catch (error) {
            showAppToast(error.message || "تعذر إضافة المنتج.", "danger");
        }
    }

    async function handleCartIncrement(button) {
        const id = Number(button.dataset.productId || 0);
        if (!id) return;

        try {
            await incrementOfflineCartItem(id);
            await refreshOfflineCartUI();
        } catch (error) {
            showAppToast(error.message || "تعذر زيادة الكمية.", "danger");
        }
    }

    async function handleCartDecrement(button) {
        const id = Number(button.dataset.productId || 0);
        if (!id) return;

        try {
            await decrementOfflineCartItem(id);
            await refreshOfflineCartUI();
        } catch (error) {
            showAppToast(error.message || "تعذر إنقاص الكمية.", "danger");
        }
    }

    async function handleCartRemove(button) {
        const id = Number(button.dataset.productId || 0);
        if (!id) return;

        try {
            await deleteOfflineCartItem(id);
            await refreshOfflineCartUI();
        } catch (error) {
            showAppToast(error.message || "تعذر حذف العنصر.", "danger");
        }
    }

    async function handleBarcodeSubmit() {
        const barcodeInput = document.getElementById("barcode-input");
        const barcodeBtn = document.getElementById("offline-barcode-submit-btn");
        const barcodeValue = (barcodeInput?.value || "").trim();

        if (!barcodeValue) {
            showAppToast("أدخل باركود أولًا.", "warning");
            return;
        }

        try {
            setButtonLoading(barcodeBtn, true, "جارٍ الإضافة...");

            const product = await getOfflineProductByBarcode(barcodeValue);

            if (!product) {
                showAppToast("لا يوجد منتج مطابق لهذا الباركود في البيانات المحلية.", "warning");
                barcodeInput.focus();
                barcodeInput.select();
                return;
            }

            await addOfflineProductToCart(product);
            await refreshOfflineCartUI();

            barcodeInput.value = "";
            barcodeInput.focus();
            showAppToast("تمت إضافة المنتج من الباركود.", "success", 1200);
        } catch (error) {
            showAppToast(error.message || "تعذر إضافة المنتج من الباركود.", "danger");
        } finally {
            setButtonLoading(barcodeBtn, false);
        }
    }

    async function autoSyncIfPossible() {
        try {
            if (typeof isBrowserOnline !== "function" || !isBrowserOnline()) {
                return;
            }

            if (typeof isOfflineSyncInProgress === "function" && isOfflineSyncInProgress()) {
                return;
            }

            const summary = await getOfflineQueueSummary();
            const pending = Number(summary.pending_sales_count || 0);
            const failed = Number(summary.failed_sales_count || 0);

            if (pending === 0 && failed === 0) {
                return;
            }

            await handleSync(false);
        } catch (error) {
            console.error("Auto sync failed:", error);
        }
    }

    async function handleCheckout() {
        const paymentType = document.getElementById("payment-type");
        const paymentCurrency = document.getElementById("payment-currency");
        const discountAmount = document.getElementById("discount-amount");
        const notes = document.getElementById("checkout-notes");
        const checkoutBtn = document.getElementById("offline-checkout-btn");

        const cart = await getAllOfflineCartItems();

        if (!cart.length) {
            showAppToast("السلة فارغة.", "warning");
            return;
        }

        if (!paymentType || paymentType.value !== "cash") {
            showAppToast("الأوفلاين يدعم البيع النقدي فقط في هذه المرحلة.", "warning");
            return;
        }

        try {
            setButtonLoading(checkoutBtn, true, "جارٍ الحفظ...");

            let exchangeRate = 1;
            const currencyCode = paymentCurrency ? paymentCurrency.value : "USD";

            const db = await openOfflineDB();
            const rates = await getAllFromStore(db, STORE_EXCHANGE_RATES);

            if (currencyCode !== "USD") {
                const matchedRate = rates.find(r =>
                    r.base_currency === "USD" && r.quote_currency === currencyCode
                );

                if (!matchedRate) {
                    showAppToast("لا يوجد سعر صرف محلي لهذه العملة.", "warning");
                    return;
                }

                exchangeRate = Number(matchedRate.rate || 1);
            }

            const record = await createOfflineCashSale({
                pricing_currency: "USD",
                payment_currency: currencyCode,
                exchange_rate: exchangeRate,
                discount_amount: Number(discountAmount?.value || 0),
                notes: notes?.value || ""
            });

            await refreshOfflineCartUI();
            await updateOfflineQueueBadge();

            showAppToast(`تم حفظ البيع الأوفلاين بنجاح - ${record.offline_id}`, "success", 3500);

            setTimeout(async () => {
                await autoSyncIfPossible();
            }, 800);

        } catch (error) {
            showAppToast(error.message || "تعذر حفظ البيع الأوفلاين.", "danger", 3500);
        } finally {
            setButtonLoading(checkoutBtn, false);
        }
    }

    async function handleSync(showAlerts = true) {
        if (typeof isOfflineSyncInProgress === "function" && isOfflineSyncInProgress()) {
            if (showAlerts) showAppToast("هناك مزامنة جارية بالفعل.", "warning");
            return;
        }

        if (typeof isBrowserOnline === "function" && !isBrowserOnline()) {
            if (showAlerts) showAppToast("لا يمكن تنفيذ المزامنة أثناء عدم وجود اتصال بالإنترنت.", "warning");
            return;
        }

        const syncBtn = document.getElementById("sync-offline-sales-btn");

        if (typeof setOfflineSyncInProgress === "function") {
            setOfflineSyncInProgress(true);
        }

        updateSyncStatusBadge("جارٍ المزامنة...", "info");
        setButtonLoading(syncBtn, true, "جارٍ المزامنة...");

        try {
            const syncUrl = window.POS_SYNC_URL || "";
            const result = await syncPendingOfflineSales(syncUrl);
            await updateOfflineQueueBadge();

            if (result.pending_count_before_sync === 0) {
                updateSyncStatusBadge("لا توجد عمليات مؤهلة للمزامنة", "warning");
                if (showAlerts) showAppToast("لا توجد عمليات مؤهلة للمزامنة.", "warning");
                return;
            }

            if (result.synced_count > 0 && result.failed_count === 0) {
                updateSyncStatusBadge(`تمت مزامنة ${result.synced_count} عملية`, "success");
                if (showAlerts) showAppToast(`تمت مزامنة ${result.synced_count} عملية بنجاح.`, "success", 3500);
                return;
            }

            if (result.synced_count > 0 && result.failed_count > 0) {
                updateSyncStatusBadge(`نجحت ${result.synced_count} وفشلت ${result.failed_count}`, "warning");
                if (showAlerts) showAppToast(`تمت مزامنة ${result.synced_count} عملية، وفشل ${result.failed_count} عملية.`, "warning", 4000);
                console.log("Sync results:", result.results);
                return;
            }

            if (result.synced_count === 0 && result.failed_count > 0) {
                if (result.blocked_count > 0) {
                    updateSyncStatusBadge(`محجوب: ${result.blocked_count}`, "danger");
                    if (showAlerts) showAppToast("فشلت العمليات، وبعضها أصبح محجوبًا بعد تكرار الفشل.", "danger", 4000);
                } else {
                    updateSyncStatusBadge(`فشل ${result.failed_count} عملية`, "danger");
                    if (showAlerts) showAppToast("فشلت جميع العمليات المعلقة في المزامنة.", "danger", 4000);
                }
                console.log("Sync results:", result.results);
            }
        } catch (error) {
            console.error(error);
            updateSyncStatusBadge("فشلت المزامنة", "danger");
            if (showAlerts) showAppToast(error.message || "حدث خطأ أثناء المزامنة.", "danger", 4000);
        } finally {
            if (typeof setOfflineSyncInProgress === "function") {
                setOfflineSyncInProgress(false);
            }
            setButtonLoading(syncBtn, false);
            await updateOfflineQueueBadge();
        }
    }

    function bindSearch() {
        const searchInput = document.getElementById("pos-search-input");
        if (!searchInput || searchInput.dataset.bound === "true") return;

        searchInput.addEventListener("input", async function () {
            const results = await searchOfflineProducts(this.value || "");
            renderProducts(results);
        });

        searchInput.dataset.bound = "true";
    }

    function bindButtons() {
        const barcodeBtn = document.getElementById("offline-barcode-submit-btn");
        const checkoutBtn = document.getElementById("offline-checkout-btn");
        const syncBtn = document.getElementById("sync-offline-sales-btn");

        if (barcodeBtn && barcodeBtn.dataset.bound !== "true") {
            barcodeBtn.addEventListener("click", handleBarcodeSubmit);
            barcodeBtn.dataset.bound = "true";
        }

        if (checkoutBtn && checkoutBtn.dataset.bound !== "true") {
            checkoutBtn.addEventListener("click", handleCheckout);
            checkoutBtn.dataset.bound = "true";
        }

        if (syncBtn && syncBtn.dataset.bound !== "true") {
            syncBtn.addEventListener("click", async function () {
                await handleSync(true);
            });
            syncBtn.dataset.bound = "true";
        }
    }

    function bindDocumentClicks() {
        if (document.body.dataset.posEngineBound === "true") return;

        document.addEventListener("click", function (e) {
            const addBtn = e.target.closest(".offline-add-to-cart-btn");
            if (addBtn) {
                e.preventDefault();
                handleAddToCart(addBtn);
                return;
            }

            const incBtn = e.target.closest(".offline-cart-increment-btn");
            if (incBtn) {
                e.preventDefault();
                handleCartIncrement(incBtn);
                return;
            }

            const decBtn = e.target.closest(".offline-cart-decrement-btn");
            if (decBtn) {
                e.preventDefault();
                handleCartDecrement(decBtn);
                return;
            }

            const removeBtn = e.target.closest(".offline-cart-remove-btn");
            if (removeBtn) {
                e.preventDefault();
                handleCartRemove(removeBtn);
                return;
            }
        });

        document.body.dataset.posEngineBound = "true";
    }

    function bindOnlineListener() {
        if (window.__posOnlineListenerBound) return;

        window.addEventListener("online", async function () {
            updateSyncStatusBadge("تم استعادة الاتصال", "success");
            await updateOfflineQueueBadge();

            setTimeout(async () => {
                await autoSyncIfPossible();
            }, 1200);
        });

        window.__posOnlineListenerBound = true;
    }

    async function init() {
        try {
            const mode = getMode();

            if (mode !== "offline") {
                return;
            }

            const products = await searchOfflineProducts("");
            renderProducts(products);

            await refreshOfflineCartUI();
            await updateOfflineQueueBadge();

            bindSearch();
            bindButtons();
            bindDocumentClicks();
            bindOnlineListener();

            if (typeof isBrowserOnline === "function" && isBrowserOnline()) {
                setTimeout(async () => {
                    await autoSyncIfPossible();
                }, 1200);
            }
        } catch (error) {
            console.error("POS ENGINE INIT FAILED:", error);

            const container = document.getElementById("offline-products-container");
            if (container) {
                container.innerHTML = `
                    <div class="list-group-item text-danger text-center">
                        فشل تحميل البيانات (Offline Engine Error)
                    </div>
                `;
            }

            showAppToast("فشل تحميل بيانات الأوفلاين.", "danger", 4000);
        }
    }

    window.POS_ENGINE = {
        init,
        renderProducts,
        updateOfflineQueueBadge,
        updateSyncStatusBadge,
        handleSync,
        autoSyncIfPossible
    };
})();