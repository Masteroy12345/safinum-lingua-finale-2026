// Safinum Lingua — Pont vocal navigateur (MAIN world) pour safinum.cm
// Enregistre les voix camerounaises auprès de window.speechSynthesis afin que le
// simulateur Web/Mobile SAFINUM reconnaisse la voix exacte (supprime l'alerte
// « Aucune voix ... sur ce navigateur ») et redirige la lecture vers l'audio
// masculin unifié ElevenLabs / Studio (avec décomposition dynamique des téléphones).
(() => {
  "use strict";
  if (window.__safinumVoiceBridgeInstalled || !("speechSynthesis" in window)) return;
  window.__safinumVoiceBridgeInstalled = true;

  const TTS_ENDPOINTS = [
    "https://maryellen-parchable-gertude.ngrok-free.dev/api/audio/tts",
    "http://127.0.0.1:3000/api/audio/tts",
  ];

  const VIRTUAL_VOICES = [
    { name: "Safinum Lingua — Duálá (Voix Homme)", lang: "dua", code: "dua" },
    { name: "Safinum Lingua — Ewondo (Voix Homme)", lang: "ewo", code: "ewo" },
    { name: "Safinum Lingua — Ɓasaá (Voix Homme)", lang: "bas", code: "bas" },
    { name: "Safinum Lingua — Ghɔmálá' (Voix Homme)", lang: "bbj", code: "bbj" },
    { name: "Safinum Lingua — Mə̀dûmbà (Voix Homme)", lang: "byv", code: "byv" },
    { name: "Safinum Lingua — Fulfulde (Voix Homme)", lang: "ff", code: "fub" },
    { name: "Safinum Lingua — Hausa (Voix Homme)", lang: "ha", code: "hau" },
    { name: "Safinum Lingua — Bulu (Voix Homme)", lang: "bum", code: "bum" },
    { name: "Safinum Lingua — Pidgin Camerounais (Voix Homme)", lang: "wes", code: "wes" },
  ].map((v) => ({
    default: false,
    lang: v.lang,
    localService: true,
    name: v.name,
    voiceURI: `safinum-lingua:${v.code}`,
    _safinumCode: v.code,
  }));

  const BY_URI = Object.fromEntries(VIRTUAL_VOICES.map((v) => [v.voiceURI, v]));
  const BY_LANG = Object.fromEntries(VIRTUAL_VOICES.map((v) => [v.lang.toLowerCase(), v]));

  const synth = window.speechSynthesis;
  const origGetVoices = synth.getVoices.bind(synth);
  const origSpeak = synth.speak.bind(synth);
  const origCancel = synth.cancel.bind(synth);

  let activeAudio = null;
  let pendingBatch = [];
  let batchTimer = null;
  let playSeq = 0;

  function stopBridgeAudio() {
    playSeq++;
    if (batchTimer) {
      clearTimeout(batchTimer);
      batchTimer = null;
    }
    pendingBatch = [];
    if (activeAudio) {
      try {
        activeAudio.pause();
        activeAudio.currentTime = 0;
      } catch {}
      activeAudio = null;
    }
  }

  async function playSafinumTTS(text, langCode, rate, lastUtterance) {
    const seq = ++playSeq;
    const clean = (text || "").replace(/\s+/g, " ").trim();
    if (!clean) {
      if (lastUtterance && typeof lastUtterance.onend === "function") lastUtterance.onend(new Event("end"));
      return;
    }
    for (const url of TTS_ENDPOINTS) {
      if (seq !== playSeq) return;
      try {
        const resp = await fetch(url, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ text: clean, language: langCode || "fr" }),
        });
        if (!resp.ok || !(resp.headers.get("content-type") || "").includes("audio")) continue;
        const blob = await resp.blob();
        if (seq !== playSeq) return;
        const objUrl = URL.createObjectURL(blob);
        const audio = new Audio(objUrl);
        audio.playbackRate = Number(rate) || 0.95;
        activeAudio = audio;
        const finish = () => {
          URL.revokeObjectURL(objUrl);
          if (activeAudio === audio) activeAudio = null;
          if (lastUtterance && typeof lastUtterance.onend === "function") lastUtterance.onend(new Event("end"));
        };
        audio.onended = finish;
        audio.onerror = finish;
        await audio.play();
        return;
      } catch {
        // Essayer l'endpoint suivant
      }
    }
    if (lastUtterance && typeof lastUtterance.onerror === "function") lastUtterance.onerror(new Event("error"));
  }

  synth.getVoices = function getVoicesWithSafinum() {
    const native = origGetVoices() || [];
    const existingUris = new Set(native.map((v) => v.voiceURI));
    const extras = VIRTUAL_VOICES.filter((v) => !existingUris.has(v.voiceURI));
    return [...extras, ...native];
  };

  synth.cancel = function cancelWithSafinum() {
    stopBridgeAudio();
    return origCancel();
  };

  synth.speak = function speakWithSafinum(utterance) {
    const vUri = utterance?.voice?.voiceURI || "";
    const vLang = (utterance?.voice?.lang || utterance?.lang || "").toLowerCase();
    const matched = BY_URI[vUri] || BY_LANG[vLang];
    if (!matched) {
      return origSpeak(utterance);
    }
    pendingBatch.push({
      text: utterance.text || "",
      langCode: matched._safinumCode,
      rate: utterance.rate || 0.95,
      utterance,
    });
    if (!batchTimer) {
      batchTimer = setTimeout(() => {
        const batch = pendingBatch.slice();
        pendingBatch = [];
        batchTimer = null;
        if (!batch.length) return;
        const fullText = batch.map((b) => b.text).filter(Boolean).join(". ");
        const last = batch[batch.length - 1];
        playSafinumTTS(fullText, last.langCode, last.rate, last.utterance);
      }, 25);
    }
  };

  setTimeout(() => {
    try {
      synth.dispatchEvent(new Event("voiceschanged"));
    } catch {}
  }, 50);
})();
