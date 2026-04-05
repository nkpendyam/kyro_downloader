const KYRO_API_URL = "http://localhost:8000";

chrome.runtime.onInstalled.addListener(() => {
  chrome.contextMenus.create({
    id: "kyro-download",
    title: "Download with Kyro",
    contexts: ["link", "selection", "page"],
  });
  chrome.contextMenus.create({
    id: "kyro-mp3",
    title: "Download as MP3 with Kyro",
    contexts: ["link", "selection"],
  });
});

chrome.contextMenus.onClicked.addListener((info, tab) => {
  let url = info.linkUrl || info.selectionText || tab.url;
  if (!url) return;

  if (info.menuItemId === "kyro-mp3") {
    sendToKyro(url, { mode: "mp3" });
  } else {
    sendToKyro(url, {});
  }
});

async function sendToKyro(url, options) {
  try {
    const payload = {
      url,
      only_audio: options.mode === "mp3",
      audio_format: options.mode === "mp3" ? "mp3" : "mp3",
      audio_quality: options.mode === "mp3" ? "192" : "192",
      priority: "normal",
    };

    const response = await fetch(`${KYRO_API_URL}/api/download`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    if (response.ok) {
      chrome.notifications.create({
        type: "basic",
        iconUrl: "icons/icon128.png",
        title: "Kyro Downloader",
        message: `Queued: ${url.substring(0, 50)}...`,
      });
    } else {
      throw new Error(`HTTP ${response.status}`);
    }
  } catch (error) {
    chrome.notifications.create({
      type: "basic",
      iconUrl: "icons/icon128.png",
      title: "Kyro Downloader",
      message: `Failed: ${error.message}. Is Kyro running?`,
    });
  }
}

chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === "download") {
    sendToKyro(request.url, request.options || {});
    sendResponse({ status: "queued" });
  }
});
