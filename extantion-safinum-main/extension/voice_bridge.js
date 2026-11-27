// Safinum Lingua v0.9.0 — Pont vocal (MAIN world) pour safinum.cm
//
// OPTIMISATIONS LATENCE v0.9 :
// 1. Cache navigateur : le WAV est mis en cache (Map en mémoire) → 0ms sur répétition
// 2. Préchauffe : le texte affiché est pré-synthétisé 1s après chargement de la page
// 3. Batch timer réduit à 0ms (microtask) pour démarrer sans délai
// 4. Streaming WAV : on joue dès l'arrivée du blob sans attendre la fin du buffer
(() => {
  "use strict";
  if (window.__safinumVoiceBridgeInstalled || !("speechSynthesis" in window)) return;
  window.__safinumVoiceBridgeInstalled = true;

  const TTS_ENDPOINTS = [
    // 1. Vercel permanent (compte raveliop12345, jamais expiré)
    "https://safinum-tts-v2.vercel.app/api/tts",
    // 2. ngrok (middleware local, backup)
    "https://maryellen-parchable-gertude.ngrok-free.dev/api/audio/tts",
    // 3. localhost (dev local)
    "http://127.0.0.1:3000/api/audio/tts",
  ];

  // Mapping sandbox : yt = {fr:"fr-FR", en:"en-US", fub:"ff", hau:"ha"}
  const LANG_DEFS = [
    { code: "dua", langs: ["dua", "dua-CM"],        name: "Duálá (Safinum)",       fallbackLang: "fr-FR" },
    { code: "ewo", langs: ["ewo", "ewo-CM"],        name: "Ewondo (Safinum)",       fallbackLang: "fr-FR" },
    { code: "bas", langs: ["bas", "bas-CM"],        name: "Ɓasaá (Safinum)",        fallbackLang: "fr-FR" },
    { code: "bbj", langs: ["bbj", "bbj-CM"],        name: "Ghɔmálá' (Safinum)",     fallbackLang: "fr-FR" },
    { code: "byv", langs: ["byv", "byv-CM"],        name: "Mə̀dûmbà (Safinum)",     fallbackLang: "fr-FR" },
    { code: "fub", langs: ["fub", "fub-CM", "ff"],  name: "Fulfulde (Safinum)",     fallbackLang: "fr-FR" },
    { code: "hau", langs: ["hau", "hau-CM", "ha"],  name: "Haoussa (Safinum)",      fallbackLang: "fr-FR" },
    { code: "bum", langs: ["bum", "bum-CM"],        name: "Bulu (Safinum)",         fallbackLang: "fr-FR" },
    { code: "wes", langs: ["wes", "wes-CM"],        name: "Pidgin (Safinum)",       fallbackLang: "en-US" },
  ];

  const TAG_TO_CODE = {};
  const TAG_TO_DEF = {};
  for (const d of LANG_DEFS) {
    for (const l of d.langs) {
      TAG_TO_CODE[l.toLowerCase()] = d.code;
      TAG_TO_DEF[l.toLowerCase()] = d;
    }
  }

  function resolveLang(tag) {
    if (!tag) return null;
    const lc = String(tag).toLowerCase().replace("_", "-");
    return TAG_TO_CODE[lc] || TAG_TO_CODE[lc.split("-")[0]] || null;
  }

  function resolveDef(code) {
    return LANG_DEFS.find((d) => d.code === code) || null;
  }

  // ─── Intercepter le setter .voice AVANT que Chrome plante ───────────────────
  const UtteranceProto = window.SpeechSynthesisUtterance.prototype;
  const origVoiceDesc = Object.getOwnPropertyDescriptor(UtteranceProto, "voice");

  Object.defineProperty(UtteranceProto, "voice", {
    get() {
      return this.__safinumVoiceObj ?? (origVoiceDesc?.get ? origVoiceDesc.get.call(this) : null);
    },
    set(v) {
      if (!v) {
        this.__safinumLangCode = null;
        this.__safinumVoiceObj = null;
        try { origVoiceDesc?.set?.call(this, null); } catch {}
        return;
      }
      let langTag = null;
      try { langTag = v.lang; } catch {}
      const code = resolveLang(langTag);

      if (code) {
        // Voix Safinum → capturer, NE PAS transmettre (Chrome planterait)
        this.__safinumLangCode = code;
        this.__safinumVoiceObj = v;
        console.info("[Safinum] .voice capturé →", code, "(bloqué avant Chrome)");
        return;
      }
      // Voix native étrangère
      this.__safinumLangCode = null;
      this.__safinumVoiceObj = null;
      try { origVoiceDesc?.set?.call(this, v); } catch {}
    },
    configurable: true,
    enumerable: true,
  });

  // ─── getVoices() ─────────────────────────────────────────────────────────────
  const synth = window.speechSynthesis;
  const origGetVoices = synth.getVoices.bind(synth);
  const origSpeak = synth.speak.bind(synth);
  const origCancel = synth.cancel.bind(synth);

  const safinumDescriptors = LANG_DEFS.flatMap((def) =>
    def.langs.map((langTag) => ({
      lang: langTag,
      name: def.name,
      voiceURI: "safinum-" + def.code,
      localService: true,
      default: false,
      _safinumCode: def.code,
      toString() { return def.name; },
    }))
  );

  synth.getVoices = function getVoicesWithSafinum() {
    const native = origGetVoices() || [];
    return [...native, ...safinumDescriptors];
  };

  // ─── Cache WAV en mémoire (clé = "lang|texte") ──────────────────────────────
  const WAV_CACHE = new Map();      // clé → ObjectURL (encore valide)
  const WAV_CACHE_MAX = 40;

  function cacheGet(text, lang) {
    return WAV_CACHE.get(lang + "|" + text) || null;
  }
  function cachePut(text, lang, url) {
    if (WAV_CACHE.size >= WAV_CACHE_MAX) {
      // Supprimer la plus ancienne entrée
      const oldest = WAV_CACHE.keys().next().value;
      try { URL.revokeObjectURL(WAV_CACHE.get(oldest)); } catch {}
      WAV_CACHE.delete(oldest);
    }
    WAV_CACHE.set(lang + "|" + text, url);
  }

  // ─── TTS API avec cache, logs et fallback ───────────────────────────────────
  let activeAudio = null;
  let playSeq = 0;
  let pendingBatch = [];
  let batchTimer = null;

  function stopBridgeAudio() {
    playSeq++;
    if (batchTimer) { clearTimeout(batchTimer); batchTimer = null; }
    pendingBatch = [];
    if (activeAudio) {
      try { activeAudio.pause(); activeAudio.currentTime = 0; } catch {}
      activeAudio = null;
    }
  }

  async function playSafinumTTS(text, langCode, rate, lastUtterance) {
    const seq = ++playSeq;
    const clean = (text || "").replace(/\s+/g, " ").trim();
    if (!clean) { lastUtterance?.onend?.(new Event("end")); return; }

    // ── 1. Cache hit : lecture instantanée (0ms réseau) ──────────────────────
    const cached = cacheGet(clean, langCode);
    if (cached) {
      console.info("[Safinum] cache hit →", langCode);
      const audio = new Audio(cached);
      audio.playbackRate = Number(rate) || 0.95;
      activeAudio = audio;
      const done = () => { if (activeAudio === audio) activeAudio = null; lastUtterance?.onend?.(new Event("end")); };
      audio.onended = done; audio.onerror = done;
      await audio.play().catch(() => done());
      return;
    }

    console.info("[Safinum] TTS →", { text: clean.slice(0, 60), langCode });

    for (const url of TTS_ENDPOINTS) {
      if (seq !== playSeq) return;
      try {
        const resp = await fetch(url, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ text: clean, language: langCode }),
        });
        const ct = resp.headers.get("content-type") || "";
        console.info("[Safinum] fetch", url, "→ HTTP", resp.status, ct);
        if (!resp.ok || !ct.includes("audio")) {
          // Si l'API retourne du JSON (fallback phonétique), lire avec le browser TTS
          if (ct.includes("json")) {
            const data = await resp.json().catch(() => null);
            console.info("[Safinum] JSON fallback reçu :", data);
            if (data?.tts_script || data?.web_phonetic) {
              playBrowserFallback(data.tts_script || data.web_phonetic, data.tts_voice_lang || "fr-FR", rate, lastUtterance);
              return;
            }
          }
          continue;
        }
        const blob = await resp.blob();
        if (seq !== playSeq) return;
        const objUrl = URL.createObjectURL(blob);
        // Mettre en cache pour la prochaine lecture
        cachePut(clean, langCode, objUrl);
        const audio = new Audio(objUrl);
        audio.playbackRate = Number(rate) || 0.95;
        activeAudio = audio;
        const done = () => {
          URL.revokeObjectURL(objUrl);
          if (activeAudio === audio) activeAudio = null;
          lastUtterance?.onend?.(new Event("end"));
        };
        audio.onended = done;
        audio.onerror = (e) => { console.warn("[Safinum] audio error", e); done(); };
        await audio.play();
        return;
      } catch (err) {
        console.warn("[Safinum] fetch échoué pour", url, ":", err.message);
      }
    }

    // Fallback navigateur si les deux endpoints échouent (CSP, réseau hors-ligne)
    console.warn("[Safinum] Les deux endpoints TTS ont échoué — fallback browser TTS");
    const def = resolveDef(langCode);
    playBrowserFallback(clean, def?.fallbackLang || "fr-FR", rate, lastUtterance);
  }

  function playBrowserFallback(text, bcp47, rate, lastUtterance) {
    try {
      const u = new SpeechSynthesisUtterance(text);
      u.lang = bcp47;
      u.rate = rate || 0.95;
      u.onend = () => lastUtterance?.onend?.(new Event("end"));
      u.onerror = () => lastUtterance?.onerror?.(new Event("error"));
      origSpeak(u);
    } catch (e) {
      console.warn("[Safinum] browser fallback échoué :", e);
      lastUtterance?.onerror?.(new Event("error"));
    }
  }

  synth.speak = function speakWithSafinum(utterance) {
    const langCode =
      utterance.__safinumLangCode ||
      resolveLang(utterance?.voice?._safinumCode) ||
      resolveLang(utterance?.voice?.lang) ||
      resolveLang(utterance?.lang);

    console.info("[Safinum] speak() →", {
      langCode,
      captured: utterance.__safinumLangCode,
      voiceLang: utterance?.voice?.lang,
      voiceCode: utterance?.voice?._safinumCode,
      uttLang: utterance?.lang,
      text: (utterance?.text || "").slice(0, 50),
    });

    if (!langCode) return origSpeak(utterance);

    pendingBatch.push({
      text: utterance.text || "",
      langCode,
      rate: utterance.rate || 0.95,
      utterance,
    });
    if (!batchTimer) {
      batchTimer = setTimeout(() => {
        const batch = pendingBatch.slice();
        pendingBatch = [];
        batchTimer = null;
        if (!batch.length) return;
        // Prendre le dernier item comme source du lang/rate
        const last = batch[batch.length - 1];
        // Construire le texte : si trop long, ne garder que les derniers items
        // (le plus récent = l'écran actuel, les premiers = anciens tours déjà lus)
        let fullText = "";
        for (let i = batch.length - 1; i >= 0; i--) {
          const candidate = batch[i].text;
          if (!candidate) continue;
          const joined = candidate + (fullText ? ". " + fullText : "");
          if (joined.length > 900) break; // Rester sous la limite Vercel
          fullText = joined;
        }
        if (!fullText && last.text) fullText = last.text.slice(0, 900);
        if (!fullText) return;
        playSafinumTTS(fullText, last.langCode, last.rate, last.utterance);
      }, 0);
    }
  };

  synth.cancel = function cancelWithSafinum() {
    stopBridgeAudio();
    origCancel();
  };

  // ─── voiceschanged : tirs programmés uniquement, avec guard global ───────────
  // On NE réagit PAS à l'événement voiceschanged (ça crée une boucle).
  // On ne le déclenche qu'une seule fois au moment opportun via un flag global
  // pour ne pas interférer avec content.js qui écoute aussi cet événement.
  function fireVoicesChangedOnce() {
    if (window.__safinumVoicesFired) return;
    window.__safinumVoicesFired = true;
    try { synth.dispatchEvent(new Event("voiceschanged")); } catch {}
    // Remettre à false après 100ms pour permettre un 2e tir si nécessaire
    setTimeout(() => { window.__safinumVoicesFired = false; }, 100);
  }

  // Tirs uniquement sur setTimeout — jamais en réaction à voiceschanged
  setTimeout(fireVoicesChangedOnce, 50);
  setTimeout(fireVoicesChangedOnce, 400);
  setTimeout(fireVoicesChangedOnce, 1200);

  // ─── Préchauffe : synthétise le texte visible avant le clic 🔊 ───────────────
  // 1 seconde après le chargement, on envoie le texte de l'écran actuel à l'API.
  // Le WAV arrive dans le cache avant que l'utilisateur clique → lecture instantanée.
  function prefetchCurrentScreen() {
    let langCode = null;
    try {
      const stored = localStorage.getItem("safinum_voice") || localStorage.getItem("ttsVoice") || "";
      langCode = resolveLang(stored);
    } catch {}
    if (!langCode) return;

    const mainEl = document.querySelector("main, [role='main'], .channel-screen, .screen-content");
    const text = (mainEl?.innerText || document.body?.innerText || "").replace(/\s+/g, " ").trim().slice(0, 300);
    if (!text || cacheGet(text, langCode)) return;

    console.info("[Safinum] préchauffe →", langCode, text.slice(0, 50));

    // Préchauffe : fetch le MP3 directement pour le mettre en cache côté navigateur
    for (const url of TTS_ENDPOINTS) {
      fetch(url, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text, language: langCode }),
      })
        .then((r) => r.ok && r.headers.get("content-type")?.includes("audio") ? r.blob() : null)
        .then((blob) => {
          if (!blob) return;
          const objUrl = URL.createObjectURL(blob);
          cachePut(text, langCode, objUrl);
          console.info("[Safinum] préchauffe OK, cache prêt →", langCode);
        })
        .catch(() => {});
      break;
    }
  }

  setTimeout(prefetchCurrentScreen, 1000);
  // Re-préchauffe à chaque changement d'URL (navigation SPA)
  let _lastHref = location.href;
  setInterval(() => {
    if (location.href !== _lastHref) {
      _lastHref = location.href;
      setTimeout(prefetchCurrentScreen, 800);
    }
  }, 500);
})();
