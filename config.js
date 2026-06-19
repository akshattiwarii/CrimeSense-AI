(() => {
  const localHosts = new Set(["localhost", "127.0.0.1", "0.0.0.0"]);
  window.CRIMESENSE_API_BASE_URL = localHosts.has(window.location.hostname)
    ? ""
    : "https://crimesense-ai.onrender.com";
})();
