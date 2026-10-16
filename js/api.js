/* Клиент REST API. Результат призыва, боя и наград приходит только с сервера. */
class ApiError extends Error {
  constructor(code, message, status) { super(message); this.code = code; this.status = status; }
}

const Api = (() => {
  const tg = window.Telegram && window.Telegram.WebApp;
  const initData = tg && tg.initData ? tg.initData : "";
  const devUser = new URLSearchParams(location.search).get("dev_user");

  async function call(method, path, body) {
    const headers = { "Content-Type": "application/json" };
    if (initData) headers["X-Telegram-Init-Data"] = initData;
    if (devUser) headers["X-Dev-User"] = devUser;
    let res;
    try {
      res = await fetch("/api" + path, { method, headers, body: body === undefined ? undefined : JSON.stringify(body) });
    } catch (e) {
      throw new ApiError("network", "Нет соединения с сервером. Проверьте сеть и повторите.", 0);
    }
    let data = null;
    try { data = await res.json(); } catch (e) { /* не JSON */ }
    if (!res.ok) {
      const err = data && data.error;
      throw new ApiError(err ? err.code : "http_" + res.status,
        err ? err.message : "Ошибка сервера (" + res.status + ").", res.status);
    }
    return data;
  }

  function uuid() {
    if (window.crypto && crypto.randomUUID) return crypto.randomUUID();
    return "r" + Date.now().toString(36) + Math.random().toString(36).slice(2, 10);
  }

  return {
    hasTelegram: !!initData,
    get: (p) => call("GET", p),
    post: (p, b) => call("POST", p, b || {}),
    put: (p, b) => call("PUT", p, b || {}),
    uuid,
  };
})();
