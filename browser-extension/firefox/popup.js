document.addEventListener("DOMContentLoaded", async () => {
  const [tab] = await browser.tabs.query({ active: true, currentWindow: true });
  const urlDisplay = document.getElementById("url-display");
  const statusEl = document.getElementById("status");

  if (tab && tab.url) {
    urlDisplay.textContent = tab.url;
  }

  document.getElementById("btn-download").addEventListener("click", () => {
    sendToKyro(tab.url, {});
  });

  document.getElementById("btn-mp3").addEventListener("click", () => {
    sendToKyro(tab.url, { mode: "mp3" });
  });

  document.getElementById("btn-queue").addEventListener("click", () => {
    sendToKyro(tab.url, { queue: true });
  });

  async function sendToKyro(url, options) {
    const KYRO_API_URL = "http://localhost:8000";
    try {
      const response = await fetch(`${KYRO_API_URL}/api/queue`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ url, ...options }),
      });
      if (response.ok) {
        statusEl.textContent = "Queued successfully!";
        statusEl.className = "status success";
      } else {
        throw new Error(`HTTP ${response.status}`);
      }
    } catch (error) {
      statusEl.textContent = `Error: ${error.message}. Is Kyro running?`;
      statusEl.className = "status error";
    }
  }
});
