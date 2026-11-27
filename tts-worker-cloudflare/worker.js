/**
 * Safinum TTS Worker — Cloudflare Workers
 * Proxy ElevenLabs avec cache KV (optionnel) et CORS pour safinum.cm
 *
 * Variables d'environnement à configurer dans le dashboard Cloudflare :
 *   ELEVENLABS_API_KEY  = sk_c79053c7...
 *   ELEVENLABS_VOICE_ID = nPczCjzI2devNBz1zQrb   (Brian male)
 *   ELEVENLABS_MODEL_ID = eleven_multilingual_v2
 *
 * Deploy :
 *   npm install -g wrangler
 *   wrangler deploy
 */

const CORS = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Methods": "POST, GET, OPTIONS",
  "Access-Control-Allow-Headers": "Content-Type",
};

// Phonétique minimale : remplace les symboles AGLC que ElevenLabs ne prononce pas bien
const PHON_RULES = [
  [/ɛ/g, "è"], [/Ɛ/g, "È"],
  [/ɔ/g, "o"], [/Ɔ/g, "O"],
  [/ŋk/g, "nk"], [/ŋg/g, "ng"], [/ŋ/g, "ng"],
  [/ə/g, "e"], [/Ə/g, "E"],
  [/ʉ/g, "ou"],
  [/ɓ/g, "b"], [/ɓ/g, "B"],
  [/ɗ/g, "d"], [/ɗ/g, "D"],
  [/ʼ|'/g, ""],
];

function applyPhonetics(text) {
  let t = text;
  for (const [re, rep] of PHON_RULES) t = t.replace(re, rep);
  return t;
}

async function handleTTS(request, env) {
  let text = "", language = "fr";

  if (request.method === "POST") {
    try {
      const body = await request.json();
      text = body.text || "";
      language = body.language || "fr";
    } catch { return new Response("Bad JSON", { status: 400, headers: CORS }); }
  } else {
    const url = new URL(request.url);
    text = url.searchParams.get("text") || "";
    language = url.searchParams.get("language") || "fr";
  }

  text = text.replace(/\s+/g, " ").trim();
  if (!text) return new Response("No text", { status: 400, headers: CORS });

  // Clé de cache : hash simple
  const cacheKey = `tts:${language}:${text.slice(0, 200)}`;

  // Essayer le cache KV si disponible
  if (env.TTS_CACHE) {
    const cached = await env.TTS_CACHE.get(cacheKey, "arrayBuffer").catch(() => null);
    if (cached) {
      return new Response(cached, {
        headers: { ...CORS, "Content-Type": "audio/wav", "X-TTS-Cache": "hit", "Cache-Control": "public, max-age=86400" },
      });
    }
  }

  // Préparer le texte pour ElevenLabs
  const ttsText = applyPhonetics(text);
  const langCode = language === "wes" ? "en" : "fr"; // Pidgin → en, reste → fr

  const apiKey = env.ELEVENLABS_API_KEY;
  const voiceId = env.ELEVENLABS_VOICE_ID || "nPczCjzI2devNBz1zQrb";
  const modelId = env.ELEVENLABS_MODEL_ID || "eleven_multilingual_v2";

  if (!apiKey) {
    return new Response(JSON.stringify({ error: "ELEVENLABS_API_KEY not set" }), {
      status: 503,
      headers: { ...CORS, "Content-Type": "application/json" },
    });
  }

  try {
    const resp = await fetch(
      `https://api.elevenlabs.io/v1/text-to-speech/${voiceId}?output_format=mp3_44100_128`,
      {
        method: "POST",
        headers: { "xi-api-key": apiKey, "Content-Type": "application/json" },
        body: JSON.stringify({
          text: ttsText,
          model_id: modelId,
          language_code: langCode,
          voice_settings: { stability: 0.55, similarity_boost: 0.78, style: 0.12, use_speaker_boost: true },
        }),
      }
    );

    if (!resp.ok) {
      const err = await resp.text();
      return new Response(JSON.stringify({ error: err }), {
        status: resp.status,
        headers: { ...CORS, "Content-Type": "application/json" },
      });
    }

    const audioBuffer = await resp.arrayBuffer();

    // Mettre en cache KV (expire 24h) si disponible
    if (env.TTS_CACHE) {
      env.TTS_CACHE.put(cacheKey, audioBuffer, { expirationTtl: 86400 }).catch(() => {});
    }

    return new Response(audioBuffer, {
      headers: {
        ...CORS,
        "Content-Type": "audio/mpeg",
        "X-TTS-Engine": "elevenlabs-cloudflare",
        "Cache-Control": "public, max-age=86400",
      },
    });
  } catch (err) {
    return new Response(JSON.stringify({ error: err.message }), {
      status: 502,
      headers: { ...CORS, "Content-Type": "application/json" },
    });
  }
}

export default {
  async fetch(request, env) {
    // CORS preflight
    if (request.method === "OPTIONS") {
      return new Response(null, { status: 204, headers: CORS });
    }
    const url = new URL(request.url);
    if (url.pathname === "/api/audio/tts" || url.pathname === "/tts") {
      return handleTTS(request, env);
    }
    if (url.pathname === "/health" || url.pathname === "/") {
      return new Response(JSON.stringify({ status: "ok", service: "safinum-tts-worker" }), {
        headers: { ...CORS, "Content-Type": "application/json" },
      });
    }
    return new Response("Not found", { status: 404, headers: CORS });
  },
};
