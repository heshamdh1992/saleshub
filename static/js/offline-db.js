const OFFLINE_DB_NAME = "saleshub_offline";
const OFFLINE_DB_VERSION = 3;

const STORE_PRODUCTS = "products";
const STORE_EXCHANGE_RATES = "exchange_rates";
const STORE_META = "meta";
const STORE_OFFLINE_CART = "offline_cart";
const STORE_OFFLINE_SALES = "offline_sales";

const MAX_SYNC_ATTEMPTS = 5;

function openOfflineDB() {
    return new Promise((resolve, reject) => {
        const request = indexedDB.open(OFFLINE_DB_NAME, OFFLINE_DB_VERSION);

        request.onerror = () => reject(request.error);
        request.onsuccess = () => resolve(request.result);

        request.onupgradeneeded = (event) => {
            const db = event.target.result;

            if (!db.objectStoreNames.contains(STORE_PRODUCTS)) {
                const productsStore = db.createObjectStore(STORE_PRODUCTS, { keyPath: "id" });
                productsStore.createIndex("name", "name", { unique: false });
                productsStore.createIndex("barcode", "barcode", { unique: false });
                productsStore.createIndex("sku", "sku", { unique: false });
            }

            if (!db.objectStoreNames.contains(STORE_EXCHANGE_RATES)) {
                db.createObjectStore(STORE_EXCHANGE_RATES, { keyPath: "id" });
            }

            if (!db.objectStoreNames.contains(STORE_OFFLINE_CART)) {
                db.createObjectStore(STORE_OFFLINE_CART, { keyPath: "product_id" });
            }

            if (!db.objectStoreNames.contains(STORE_META)) {
                db.createObjectStore(STORE_META, { keyPath: "key" });
            }

            if (!db.objectStoreNames.contains(STORE_OFFLINE_SALES)) {
                const salesStore = db.createObjectStore(STORE_OFFLINE_SALES, { keyPath: "offline_id" });
                salesStore.createIndex("sync_status", "sync_status", { unique: false });
                salesStore.createIndex("created_at_local", "created_at_local", { unique: false });
            }
        };
    });
}

function clearStore(db, storeName) {
    return new Promise((resolve, reject) => {
        const tx = db.transaction(storeName, "readwrite");
        const store = tx.objectStore(storeName);
        const request = store.clear();

        request.onerror = () => reject(request.error);
        request.onsuccess = () => resolve(true);
    });
}

function bulkPut(db, storeName, items) {
    return new Promise((resolve, reject) => {
        const tx = db.transaction(storeName, "readwrite");
        const store = tx.objectStore(storeName);

        for (const item of items) {
            store.put(item);
        }

        tx.oncomplete = () => resolve(true);
        tx.onerror = () => reject(tx.error);
    });
}

function getAllFromStore(db, storeName) {
    return new Promise((resolve, reject) => {
        const tx = db.transaction(storeName, "readonly");
        const store = tx.objectStore(storeName);
        const request = store.getAll();

        request.onerror = () => reject(request.error);
        request.onsuccess = () => resolve(request.result || []);
    });
}

function putMeta(db, key, value) {
    return new Promise((resolve, reject) => {
        const tx = db.transaction(STORE_META, "readwrite");
        const store = tx.objectStore(STORE_META);
        const request = store.put({ key, value });

        request.onerror = () => reject(request.error);
        request.onsuccess = () => resolve(true);
    });
}

function getMeta(db, key) {
    return new Promise((resolve, reject) => {
        const tx = db.transaction(STORE_META, "readonly");
        const store = tx.objectStore(STORE_META);
        const request = store.get(key);

        request.onerror = () => reject(request.error);
        request.onsuccess = () => resolve(request.result ? request.result.value : null);
    });
}

function formatOfflinePrice(value) {
    const num = Number(value || 0);
    return num.toFixed(2);
}

function isBrowserOnline() {
    return navigator.onLine;
}

function getCsrfTokenFromCookie() {
    const cookieValue = document.cookie
        .split("; ")
        .find(row => row.startsWith("csrftoken="));

    return cookieValue ? cookieValue.split("=")[1] : "";
}

/* =========================
   Bootstrap / Products
========================= */

async function saveBootstrapData(payload) {
    const db = await openOfflineDB();

    await clearStore(db, STORE_PRODUCTS);
    await clearStore(db, STORE_EXCHANGE_RATES);

    await bulkPut(db, STORE_PRODUCTS, payload.products || []);
    await bulkPut(db, STORE_EXCHANGE_RATES, payload.exchange_rates || []);

    await putMeta(db, "merchant", payload.merchant || {});
    await putMeta(db, "generated_at", payload.generated_at || null);
    await putMeta(db, "counts", payload.counts || {});

    return true;
}

async function fetchAndStoreBootstrap(url) {
    const response = await fetch(url, {
        method: "GET",
        headers: {
            "X-Requested-With": "XMLHttpRequest"
        }
    });

    if (!response.ok) {
        throw new Error("تعذر تحميل بيانات الأوفلاين من السيرفر.");
    }

    const payload = await response.json();

    if (!payload.ok) {
        throw new Error("البيانات العائدة من السيرفر غير صالحة.");
    }

    await saveBootstrapData(payload);
    return payload;
}

async function searchOfflineProducts(term = "") {
    const db = await openOfflineDB();
    const products = await getAllFromStore(db, STORE_PRODUCTS);

    const q = (term || "").trim().toLowerCase();

    if (!q) return products;

    return products.filter(product => {
        const name = (product.name || "").toLowerCase();
        const barcode = (product.barcode || "").toLowerCase();
        const sku = (product.sku || "").toLowerCase();

        return (
            name.includes(q) ||
            barcode.includes(q) ||
            sku.includes(q)
        );
    });
}

async function getOfflineProductByBarcode(barcodeValue = "") {
    const db = await openOfflineDB();
    const products = await getAllFromStore(db, STORE_PRODUCTS);

    const barcode = (barcodeValue || "").trim();
    return products.find(p => (p.barcode || "") === barcode) || null;
}

async function getOfflineBootstrapInfo() {
    const db = await openOfflineDB();

    const merchant = await getMeta(db, "merchant");
    const generatedAt = await getMeta(db, "generated_at");
    const counts = await getMeta(db, "counts");

    return { merchant, generatedAt, counts };
}

/* =========================
   Product Rendering
========================= */

function renderOfflineProducts(products = []) {
    const container = document.getElementById("offline-products-container");
    const onlineContainer = document.getElementById("online-products-container");
    const offlineBadge = document.getElementById("offline-mode-badge");

    if (!container) return;

    if (onlineContainer) {
        onlineContainer.style.display = "none";
    }

    if (offlineBadge) {
        offlineBadge.classList.remove("d-none");
    }

    if (!products.length) {
        container.innerHTML = `
            <div class="list-group-item text-center text-muted">
                لا توجد منتجات متاحة محليًا
            </div>
        `;
        return;
    }

    container.innerHTML = products.map(product => `
        <div class="list-group-item py-3">
            <div class="d-flex justify-content-between align-items-center gap-2">
                <div class="flex-grow-1">
                    <div class="fw-bold">${product.name || ""}</div>
                    <small class="text-muted d-block">${product.barcode || "-"}</small>
                    <small class="text-muted d-block">المخزون: ${product.stock_quantity ?? 0}</small>
                </div>

                <div class="text-start">
                    <div class="fw-bold mb-2">$${formatOfflinePrice(product.base_price_usd)}</div>
                    <button
                        type="button"
                        class="btn btn-sm btn-outline-dark offline-add-to-cart-btn"
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

function resetToOnlineProducts() {
    const container = document.getElementById("offline-products-container");
    const onlineContainer = document.getElementById("online-products-container");
    const offlineBadge = document.getElementById("offline-mode-badge");

    if (container) container.innerHTML = "";
    if (onlineContainer) onlineContainer.style.display = "";
    if (offlineBadge) offlineBadge.classList.add("d-none");
}

async function runOfflineProductSearch(term = "") {
    const results = await searchOfflineProducts(term);
    renderOfflineProducts(results);
}

/* =========================
   Offline Cart
========================= */

async function getAllOfflineCartItems() {
    const db = await openOfflineDB();
    return await getAllFromStore(db, STORE_OFFLINE_CART);
}

async function getOfflineCartItem(productId) {
    const db = await openOfflineDB();

    return new Promise((resolve, reject) => {
        const tx = db.transaction(STORE_OFFLINE_CART, "readonly");
        const store = tx.objectStore(STORE_OFFLINE_CART);
        const request = store.get(productId);

        request.onerror = () => reject(request.error);
        request.onsuccess = () => resolve(request.result || null);
    });
}

async function putOfflineCartItem(item) {
    const db = await openOfflineDB();

    return new Promise((resolve, reject) => {
        const tx = db.transaction(STORE_OFFLINE_CART, "readwrite");
        const store = tx.objectStore(STORE_OFFLINE_CART);
        const request = store.put(item);

        request.onerror = () => reject(request.error);
        request.onsuccess = () => resolve(true);
    });
}

async function deleteOfflineCartItem(productId) {
    const db = await openOfflineDB();

    return new Promise((resolve, reject) => {
        const tx = db.transaction(STORE_OFFLINE_CART, "readwrite");
        const store = tx.objectStore(STORE_OFFLINE_CART);
        const request = store.delete(productId);

        request.onerror = () => reject(request.error);
        request.onsuccess = () => resolve(true);
    });
}

async function clearOfflineCart() {
    const db = await openOfflineDB();
    await clearStore(db, STORE_OFFLINE_CART);
    return true;
}

async function addOfflineProductToCart(product) {
    if (!product || !product.id) {
        throw new Error("المنتج غير صالح.");
    }

    const existing = await getOfflineCartItem(product.id);
    const stockQty = Number(product.stock_quantity || 0);

    if (stockQty <= 0) {
        throw new Error("هذا المنتج غير متوفر في المخزون.");
    }

    if (existing) {
        const nextQty = Number(existing.quantity || 0) + 1;

        if (nextQty > stockQty) {
            throw new Error("لا يمكن إضافة كمية أكبر من المخزون المتاح.");
        }

        existing.quantity = nextQty;
        await putOfflineCartItem(existing);
        return existing;
    }

    const newItem = {
        product_id: product.id,
        name: product.name || "",
        barcode: product.barcode || "",
        sku: product.sku || "",
        price: Number(product.base_price_usd || 0),
        cost: Number(product.cost_price_usd || 0),
        stock_quantity: stockQty,
        quantity: 1
    };

    await putOfflineCartItem(newItem);
    return newItem;
}

async function incrementOfflineCartItem(productId) {
    const item = await getOfflineCartItem(productId);
    if (!item) throw new Error("العنصر غير موجود في السلة.");

    const nextQty = Number(item.quantity || 0) + 1;
    const stockQty = Number(item.stock_quantity || 0);

    if (nextQty > stockQty) {
        throw new Error("لا يمكن تجاوز المخزون المتاح.");
    }

    item.quantity = nextQty;
    await putOfflineCartItem(item);
    return item;
}

async function decrementOfflineCartItem(productId) {
    const item = await getOfflineCartItem(productId);
    if (!item) throw new Error("العنصر غير موجود في السلة.");

    const nextQty = Number(item.quantity || 0) - 1;

    if (nextQty <= 0) {
        await deleteOfflineCartItem(productId);
        return null;
    }

    item.quantity = nextQty;
    await putOfflineCartItem(item);
    return item;
}

function calculateOfflineCartTotals(items = []) {
    let subtotal = 0;
    let totalCost = 0;

    for (const item of items) {
        const qty = Number(item.quantity || 0);
        const price = Number(item.price || 0);
        const cost = Number(item.cost || 0);

        subtotal += qty * price;
        totalCost += qty * cost;
    }

    const totalProfit = subtotal - totalCost;

    return {
        subtotal: subtotal.toFixed(2),
        totalCost: totalCost.toFixed(2),
        totalProfit: totalProfit.toFixed(2)
    };
}

function renderOfflineCart(items = []) {
    const cartItemsContainer = document.getElementById("cart-items-container");
    const cartSummaryContainer = document.getElementById("cart-summary-container");

    if (!cartItemsContainer || !cartSummaryContainer) return;

    if (!items.length) {
        cartItemsContainer.innerHTML = `<p class="text-muted mb-0">السلة فارغة</p>`;
        cartSummaryContainer.innerHTML = "";
        return;
    }

    const itemsHtml = items.map(item => `
        <div class="border rounded-4 p-3 mb-3 pos-cart-item">
            <div class="d-flex justify-content-between align-items-start mb-2">
                <div>
                    <div class="fw-bold fs-6">${item.name}</div>
                    <small class="text-muted">سعر الوحدة: $${formatOfflinePrice(item.price)}</small>
                </div>
                <div class="text-start fw-bold">x${item.quantity}</div>
            </div>

            <div class="row g-2 mb-2">
                <div class="col-4 d-grid">
                    <button
                        type="button"
                        class="btn btn-outline-secondary btn-lg offline-cart-decrement-btn"
                        data-product-id="${item.product_id}"
                    >-</button>
                </div>

                <div class="col-4 d-flex align-items-center justify-content-center">
                    <div class="fw-bold fs-5">${item.quantity}</div>
                </div>

                <div class="col-4 d-grid">
                    <button
                        type="button"
                        class="btn btn-outline-primary btn-lg offline-cart-increment-btn"
                        data-product-id="${item.product_id}"
                    >+</button>
                </div>
            </div>

            <button
                type="button"
                class="btn btn-outline-danger w-100 offline-cart-remove-btn"
                data-product-id="${item.product_id}"
            >حذف من السلة</button>
        </div>
    `).join("");

    cartItemsContainer.innerHTML = itemsHtml;

    const totals = calculateOfflineCartTotals(items);

    cartSummaryContainer.innerHTML = `
        <div class="pos-summary-box p-3 rounded-4">
            <div class="d-flex justify-content-between mb-2">
                <span class="fw-bold">الإجمالي</span>
                <span class="fw-bold">$${totals.subtotal}</span>
            </div>
            <div class="d-flex justify-content-between mb-2">
                <span>التكلفة</span>
                <span>$${totals.totalCost}</span>
            </div>
            <div class="d-flex justify-content-between">
                <span>الربح التقديري</span>
                <span>$${totals.totalProfit}</span>
            </div>
        </div>
    `;
}

async function refreshOfflineCartUI() {
    const items = await getAllOfflineCartItems();
    renderOfflineCart(items);
}

async function clearOfflineCartAfterCheckout() {
    await clearOfflineCart();
    await refreshOfflineCartUI();
}

async function debugOfflineState() {
    const db = await openOfflineDB();
    const products = await getAllFromStore(db, STORE_PRODUCTS);
    const cart = await getAllFromStore(db, STORE_OFFLINE_CART);
    const meta = await getMeta(db, "counts");

    return {
        productsCount: products.length,
        cartCount: cart.length,
        countsMeta: meta,
        sampleProduct: products[0] || null,
        sampleCartItem: cart[0] || null
    };
}

/* =========================
   Offline Sales Queue
========================= */

function generateOfflineSaleId() {
    const now = new Date();
    const stamp = now.getFullYear().toString() +
        String(now.getMonth() + 1).padStart(2, "0") +
        String(now.getDate()).padStart(2, "0") + "-" +
        String(now.getHours()).padStart(2, "0") +
        String(now.getMinutes()).padStart(2, "0") +
        String(now.getSeconds()).padStart(2, "0") + "-" +
        Math.random().toString(36).slice(2, 8).toUpperCase();

    return `OFFSALE-${stamp}`;
}

async function getAllOfflineSales() {
    const db = await openOfflineDB();
    return await getAllFromStore(db, STORE_OFFLINE_SALES);
}

async function getPendingOfflineSales() {
    const sales = await getAllOfflineSales();
    return sales.filter(sale => sale.sync_status === "pending");
}

async function putOfflineSaleRecord(record) {
    const db = await openOfflineDB();

    return new Promise((resolve, reject) => {
        const tx = db.transaction(STORE_OFFLINE_SALES, "readwrite");
        const store = tx.objectStore(STORE_OFFLINE_SALES);
        const request = store.put(record);

        request.onerror = () => reject(request.error);
        request.onsuccess = () => resolve(true);
    });
}

async function deleteOfflineSaleRecord(offlineId) {
    const db = await openOfflineDB();

    return new Promise((resolve, reject) => {
        const tx = db.transaction(STORE_OFFLINE_SALES, "readwrite");
        const store = tx.objectStore(STORE_OFFLINE_SALES);
        const request = store.delete(offlineId);

        request.onerror = () => reject(request.error);
        request.onsuccess = () => resolve(true);
    });
}

async function createOfflineCashSale(options = {}) {
    const items = await getAllOfflineCartItems();

    if (!items.length) {
        throw new Error("السلة فارغة.");
    }

    const discountAmount = Number(options.discount_amount || 0);
    if (discountAmount < 0) {
        throw new Error("الخصم لا يمكن أن يكون سالبًا.");
    }

    const totals = calculateOfflineCartTotals(items);
    const subtotal = Number(totals.subtotal || 0);

    if (discountAmount > subtotal) {
        throw new Error("الخصم أكبر من إجمالي الفاتورة.");
    }

    const totalAmount = Number((subtotal - discountAmount).toFixed(2));
    const exchangeRate = Number(options.exchange_rate || 1);
    const totalAmountPaymentCurrency = Number((totalAmount * exchangeRate).toFixed(2));

    const record = {
        offline_id: generateOfflineSaleId(),
        created_at_local: new Date().toISOString(),
        payment_type: "cash",
        payment_status: "paid",
        pricing_currency: options.pricing_currency || "USD",
        payment_currency: options.payment_currency || "USD",
        exchange_rate: exchangeRate,
        discount_amount: Number(discountAmount.toFixed(2)),
        subtotal: Number(subtotal.toFixed(2)),
        total_amount: totalAmount,
        total_amount_payment_currency: totalAmountPaymentCurrency,
        amount_paid: totalAmount,
        amount_due: 0,
        total_cost: Number(totals.totalCost || 0),
        total_profit: Number((totalAmount - Number(totals.totalCost || 0)).toFixed(2)),
        notes: options.notes || "",
        items: items.map(item => ({
            product_id: item.product_id,
            name: item.name,
            barcode: item.barcode,
            sku: item.sku,
            quantity: Number(item.quantity || 0),
            unit_price: Number(item.price || 0),
            unit_cost: Number(item.cost || 0),
            line_total: Number((Number(item.quantity || 0) * Number(item.price || 0)).toFixed(2))
        })),
        sync_status: "pending",
        sync_attempts: 0,
        last_sync_attempt_at: null,
        last_sync_error: "",
        synced_at: null,
        server_sale_id: null,
        server_invoice_number: null
    };

    await putOfflineSaleRecord(record);
    await clearOfflineCartAfterCheckout();

    return record;
}

async function getOfflineSaleRecord(offlineId) {
    const db = await openOfflineDB();

    return new Promise((resolve, reject) => {
        const tx = db.transaction(STORE_OFFLINE_SALES, "readonly");
        const store = tx.objectStore(STORE_OFFLINE_SALES);
        const request = store.get(offlineId);

        request.onerror = () => reject(request.error);
        request.onsuccess = () => resolve(request.result || null);
    });
}

async function updateOfflineSaleSyncFields(offlineId, updates = {}) {
    const db = await openOfflineDB();

    return new Promise((resolve, reject) => {
        const tx = db.transaction(STORE_OFFLINE_SALES, "readwrite");
        const store = tx.objectStore(STORE_OFFLINE_SALES);
        const getRequest = store.get(offlineId);

        getRequest.onerror = () => reject(getRequest.error);

        getRequest.onsuccess = () => {
            const record = getRequest.result;
            if (!record) {
                resolve(false);
                return;
            }

            Object.assign(record, updates);

            const putRequest = store.put(record);
            putRequest.onerror = () => reject(putRequest.error);
            putRequest.onsuccess = () => resolve(true);
        };
    });
}

async function markOfflineSaleAsSyncing(offlineId) {
    return await updateOfflineSaleSyncFields(offlineId, {
        sync_status: "syncing",
        last_sync_attempt_at: new Date().toISOString()
    });
}

async function markOfflineSaleAsFailed(offlineId, errorMessage = "") {
    const existing = await getOfflineSaleRecord(offlineId);
    const currentAttempts = Number(existing?.sync_attempts || 0);

    return await updateOfflineSaleSyncFields(offlineId, {
        sync_status: "failed",
        sync_attempts: currentAttempts + 1,
        last_sync_attempt_at: new Date().toISOString(),
        last_sync_error: errorMessage || "فشل غير معروف"
    });
}

async function markOfflineSaleAsSynced(offlineId, syncResult = {}) {
    const existing = await getOfflineSaleRecord(offlineId);
    const currentAttempts = Number(existing?.sync_attempts || 0);

    return await updateOfflineSaleSyncFields(offlineId, {
        sync_status: "synced",
        sync_attempts: currentAttempts + 1,
        synced_at: new Date().toISOString(),
        last_sync_attempt_at: new Date().toISOString(),
        last_sync_error: "",
        server_sale_id: syncResult.sale_id || null,
        server_invoice_number: syncResult.invoice_number || null
    });
}

async function getSyncEligibleOfflineSales() {
    const sales = await getAllOfflineSales();

    return sales.filter(sale => {
        const attempts = Number(sale.sync_attempts || 0);
        const status = sale.sync_status || "pending";

        if (status === "pending") return true;
        if (status === "failed" && attempts < MAX_SYNC_ATTEMPTS) return true;

        return false;
    });
}

async function getBlockedOfflineSales() {
    const sales = await getAllOfflineSales();

    return sales.filter(sale => {
        const attempts = Number(sale.sync_attempts || 0);
        return sale.sync_status === "failed" && attempts >= MAX_SYNC_ATTEMPTS;
    });
}

async function getFailedOfflineSales() {
    const sales = await getAllOfflineSales();
    return sales.filter(sale => sale.sync_status === "failed");
}

async function getSyncingOfflineSales() {
    const sales = await getAllOfflineSales();
    return sales.filter(sale => sale.sync_status === "syncing");
}

async function getPendingOnlyOfflineSales() {
    const sales = await getAllOfflineSales();
    return sales.filter(sale => sale.sync_status === "pending");
}

async function clearFailedOfflineSales() {
    const failedSales = await getFailedOfflineSales();

    for (const sale of failedSales) {
        await deleteOfflineSaleRecord(sale.offline_id);
    }

    return failedSales.length;
}

async function getOfflineQueueSummary() {
    const sales = await getAllOfflineSales();

    return {
        pending_sales_count: sales.filter(x => x.sync_status === "pending").length,
        syncing_sales_count: sales.filter(x => x.sync_status === "syncing").length,
        failed_sales_count: sales.filter(x => x.sync_status === "failed").length,
        blocked_sales_count: sales.filter(x => {
            const attempts = Number(x.sync_attempts || 0);
            return x.sync_status === "failed" && attempts >= MAX_SYNC_ATTEMPTS;
        }).length
    };
}

async function syncPendingOfflineSales(syncUrl) {
    await recoverStuckSyncingSales();

    const pendingSales = await getSyncEligibleOfflineSales();
    const pendingCountBeforeSync = pendingSales.length;

    if (!pendingSales.length) {
        return {
            ok: true,
            pending_count_before_sync: 0,
            synced_count: 0,
            failed_count: 0,
            blocked_count: (await getBlockedOfflineSales()).length,
            results: []
        };
    }

    for (const sale of pendingSales) {
        await markOfflineSaleAsSyncing(sale.offline_id);
    }

    let response;

    try {
        response = await fetch(syncUrl, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "X-Requested-With": "XMLHttpRequest",
                "X-CSRFToken": getCsrfTokenFromCookie()
            },
            body: JSON.stringify({
                sales: pendingSales
            })
        });
    } catch (networkError) {
        for (const sale of pendingSales) {
            await updateOfflineSaleSyncFields(sale.offline_id, {
                sync_status: "pending",
                last_sync_error: "Network disconnected before sync completed",
                last_sync_attempt_at: new Date().toISOString()
            });
        }

        throw new Error("تعذر الاتصال بالسيرفر. ما زال الإنترنت غير متوفر.");
    }

    if (!response.ok) {
        const errorText = await response.text();
        console.error("Sync HTTP error:", response.status, errorText);

        for (const sale of pendingSales) {
            await markOfflineSaleAsFailed(sale.offline_id, `HTTP ${response.status}`);
        }

        throw new Error(`فشل إرسال العمليات إلى السيرفر. HTTP ${response.status}`);
    }

    const payload = await response.json();

    if (!payload.ok) {
        for (const sale of pendingSales) {
            await markOfflineSaleAsFailed(sale.offline_id, payload.message || "فشلت المزامنة");
        }

        throw new Error(payload.message || "فشلت المزامنة.");
    }

    const results = payload.results || [];
    let syncedCount = 0;
    let failedCount = 0;

    for (const result of results) {
        if (result.ok && result.offline_id) {
            await markOfflineSaleAsSynced(result.offline_id, result);
            await deleteOfflineSaleRecord(result.offline_id);
            syncedCount += 1;
        } else if (result.offline_id) {
            await markOfflineSaleAsFailed(result.offline_id, result.message || "فشل في السيرفر");
            failedCount += 1;
        }
    }

    return {
        ok: true,
        pending_count_before_sync: pendingCountBeforeSync,
        synced_count: syncedCount,
        failed_count: failedCount,
        blocked_count: (await getBlockedOfflineSales()).length,
        results
    };
}

/* =========================
   Diagnostics
========================= */

async function debugOfflineSalesStatus() {
    const sales = await getAllOfflineSales();
    return sales.map(sale => ({
        offline_id: sale.offline_id,
        sync_status: sale.sync_status,
        sync_attempts: sale.sync_attempts,
        last_sync_attempt_at: sale.last_sync_attempt_at,
        last_sync_error: sale.last_sync_error,
        server_invoice_number: sale.server_invoice_number
    }));
}

async function debugOfflineRetryState() {
    const sales = await getAllOfflineSales();
    return sales.map(sale => ({
        offline_id: sale.offline_id,
        sync_status: sale.sync_status,
        sync_attempts: sale.sync_attempts,
        blocked: sale.sync_status === "failed" && Number(sale.sync_attempts || 0) >= MAX_SYNC_ATTEMPTS,
        last_sync_error: sale.last_sync_error,
        last_sync_attempt_at: sale.last_sync_attempt_at
    }));
}

/* =========================
   Sync Runtime State
========================= */

let offlineSyncInProgress = false;

function isOfflineSyncInProgress() {
    return offlineSyncInProgress;
}

function setOfflineSyncInProgress(value) {
    offlineSyncInProgress = Boolean(value);
}

async function recoverStuckSyncingSales() {
    const sales = await getAllOfflineSales();
    const syncingSales = sales.filter(sale => sale.sync_status === "syncing");

    for (const sale of syncingSales) {
        await updateOfflineSaleSyncFields(sale.offline_id, {
            sync_status: "pending",
            last_sync_error: "Recovered from stuck syncing state"
        });
    }

    return syncingSales.length;
}