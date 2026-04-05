(function () {
  "use strict";
  const KYRO_API_URL = "http://localhost:8000";
  const MEDIA_SELECTORS = [
    'a[href*="youtube.com/watch"]',
    'a[href*="youtu.be/"]',
    'a[href*="vimeo.com/"]',
    'a[href*="dailymotion.com/"]',
    'a[href*="twitch.tv/"]',
    'a[href*="soundcloud.com/"]',
    'a[href*="tiktok.com/"]',
    'a[href*="instagram.com/"]',
    'a[href*="twitter.com/"]',
    'a[href*="x.com/"]',
    'a[href*="reddit.com/"]',
    'a[href*="facebook.com/"]',
    'a[href*="bilibili.com/"]',
  ];

  function addKyroButton(link) {
    if (link.dataset.kyroAdded) return;
    link.dataset.kyroAdded = "true";
    const btn = document.createElement("span");
    btn.textContent = "\u2B07";
    btn.title = "Download with Kyro";
    btn.style.cssText = "display:inline-block;margin-left:4px;padding:2px 6px;background:#1a73e8;color:#fff;border-radius:3px;cursor:pointer;font-size:12px;line-height:1;vertical-align:middle;";
    btn.addEventListener("click", (e) => {
      e.preventDefault();
      e.stopPropagation();
      sendToKyro(link.href);
    });
    link.parentNode.insertBefore(btn, link.nextSibling);
  }

  async function sendToKyro(url) {
    try {
      const response = await fetch(`${KYRO_API_URL}/api/download`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          url,
          only_audio: false,
          priority: "normal",
          preset: "none",
        }),
      });
      if (response.ok) {
        showToast("Queued in Kyro: " + url.substring(0, 50) + "...");
      }
    } catch (error) {
      showToast("Kyro error: " + error.message);
    }
  }

  function showToast(message) {
    let toast = document.getElementById("kyro-toast");
    if (!toast) {
      toast = document.createElement("div");
      toast.id = "kyro-toast";
      toast.style.cssText = "position:fixed;bottom:20px;right:20px;padding:12px 20px;background:#323232;color:#fff;border-radius:8px;font-size:14px;z-index:999999;max-width:300px;box-shadow:0 4px 12px rgba(0,0,0,0.3);transition:opacity 0.3s;";
      document.body.appendChild(toast);
    }
    toast.textContent = message;
    toast.style.opacity = "1";
    clearTimeout(toast._timeout);
    toast._timeout = setTimeout(() => { toast.style.opacity = "0"; }, 3000);
  }

  function scanPage() {
    document.querySelectorAll(MEDIA_SELECTORS.join(", ")).forEach(addKyroButton);
  }

  scanPage();
  const observer = new MutationObserver(() => scanPage());
  observer.observe(document.body, { childList: true, subtree: true });
})();
