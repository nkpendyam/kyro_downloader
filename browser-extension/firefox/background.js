const KYRO_API_URL = "http://localhost:8000";

browser.runtime.onInstalled.addListener(() => {
  browser.contextMenus.create({
    id: "kyro-download",
    title: "Download with Kyro",
    contexts: ["link", "selection", "page"],
  });
  browser.contextMenus.create({
    id: "kyro-mp3",
    title: "Download as MP3 with Kyro",
    contexts: ["link", "selection"],
  });
});

browser.contextMenus.onClicked.addListener((info, tab) => {
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
    const response = await fetch(`${KYRO_API_URL}/api/queue`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ url, ...options }),
    });
    if (response.ok) {
      browser.notifications.create({
        type: "basic",
        iconUrl: "icons/icon128.png",
        title: "Kyro Downloader",
        message: `Queued: ${url.substring(0, 50)}...`,
      });
    } else {
      throw new Error(`HTTP ${response.status}`);
    }
  } catch (error) {
    browser.notifications.create({
      type: "basic",
      iconUrl: "icons/icon128.png",
      title: "Kyro Downloader",
      message: `Failed: ${error.message}. Is Kyro running?`,
    });
  }
}

browser.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === "download") {
    sendToKyro(request.url, request.options || {});
    sendResponse({ status: "queued" });
  }
});
