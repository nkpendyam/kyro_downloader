document.addEventListener("DOMContentLoaded", async () => {
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  const urlDisplay = document.getElementById("url-display");
  const statusEl = document.getElementById("status");
  const qualityEl = document.getElementById("video-quality");
  const audioFormatEl = document.getElementById("audio-format");

  if (tab && tab.url) {
    urlDisplay.textContent = tab.url;
  }

  document.getElementById("btn-download").addEventListener("click", () => {
    sendToKyro(tab.url, { quality: qualityEl.value });
  });

  document.getElementById("btn-mp3").addEventListener("click", () => {
    sendToKyro(tab.url, { mode: "mp3", audio_format: audioFormatEl.value });
  });

  document.getElementById("btn-queue").addEventListener("click", () => {
    sendToKyro(tab.url, { quality: qualityEl.value });
  });

  async function sendToKyro(url, options) {
    const KYRO_API_URL = "http://localhost:8000";
    try {
      let formatId = null;
      const quality = options.quality || "best";
      if (quality !== "best" && options.mode !== "mp3") {
        const infoResponse = await fetch(
          `${KYRO_API_URL}/api/info?url=${encodeURIComponent(url)}`
        );
        if (infoResponse.ok) {
          const info = await infoResponse.json();
          const target = parseInt(quality, 10);
          let best = null;
          for (const fmt of info.formats || []) {
            const parts = (fmt.resolution || "0x0").split("x");
            const height = parseInt(parts[1] || "0", 10);
            if (height <= target && (!best || height > best.height)) {
              best = { id: fmt.format_id, height };
            }
          }
          if (best) {
            formatId = best.id;
          }
        }
      }

      const payload = {
        url,
        format_id: formatId,
        only_audio: options.mode === "mp3",
        audio_format: options.audio_format || "mp3",
        audio_quality: options.mode === "mp3" ? "192" : "192",
        priority: "normal",
      };

      const response = await fetch(`${KYRO_API_URL}/api/download`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      if (response.ok) {
        statusEl.textContent = "Queued successfully via Web API";
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
