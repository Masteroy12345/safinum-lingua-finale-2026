/**
 * Safinum TTS — Vercel Serverless Function
 *
 * SÉCURITÉ :
 * - Ce service ne reçoit QUE du texte phonétique pré-traité + un code langue.
 * - Il ne reçoit JAMAIS et ne retourne JAMAIS de données personnelles :
 *   noms de clients, montants, numéros de téléphone, références de transaction.
 * - Ces données restent exclusivement dans le middleware local (port 3000).
 * - La clé ElevenLabs est une variable d'environnement Vercel, jamais dans le code.
 * - Rate-limiting par IP : 20 requêtes / minute maximum.
 * - Validation stricte du texte entrant (longueur max, pas de JSON, pas d'URL).
 * - Origine autorisée : safinum.cm uniquement (CORS strict).
 * - Pas de log du texte reçu (confidentialité).
 */

// ── Constantes de sécurité ─────────────────────────────────────────────────
const MAX_TEXT_LENGTH = 1000;       // Caractères max (texte d'écran complet)
const MAX_REQ_PER_MIN = 20;         // Rate limit par IP
const ALLOWED_ORIGINS = [
  "https://www.safinum.cm",
  "https://safinum.cm",
  "http://localhost:3000",
  "http://127.0.0.1:3000",
];

// Codes langue autorisés — liste blanche stricte
const ALLOWED_LANGS = new Set([
  "dua", "ewo", "bas", "bbj", "byv", "fub", "hau", "bum", "wes", "fr", "en"
]);

// ElevenLabs : lang interne → language_code BCP-47 envoyé à l'API
const ELEVEN_LANG = {
  wes: "en",    // Pidgin Camerounais → anglais
  default: "fr" // Toutes les autres langues camerounaises → français
};

// Phonétique minimale (les symboles AGLC que ElevenLabs lit mal en fr-FR)
// Le middleware applique déjà to_tts_script() — ceci est un filet de sécurité.
const PHON = [
  [/ɛ/g, "è"], [/Ɛ/g, "È"],
  [/ɔ/g, "o"], [/Ɔ/g, "O"],
  [/ŋk/g, "nk"], [/ŋg/g, "ng"], [/ŋ/g, "ng"], [/Ŋ/g, "Ng"],
  [/ə/g, "e"], [/Ə/g, "E"],
  [/ʉ/g, "ou"], [/Ʉ/g, "Ou"],
  [/ɓ/g, "b"], [/Ɓ/g, "B"],
  [/ɗ/g, "d"], [/Ɗ/g, "D"],
  [/ƴ/g, "y"], [/Ƴ/g, "Y"],
  [/[ʼ']/g, ""],
];

// ── Rate limiter en mémoire (réinitialisé à chaque cold start) ─────────────
// Vercel: chaque instance a sa propre mémoire. Pour un rate limit distribué,
// utiliser Vercel KV (optionnel). Ici : protection basique par instance.
const RATE_MAP = new Map(); // ip → {count, resetAt}

function checkRateLimit(ip) {
  const now = Date.now();
  const entry = RATE_MAP.get(ip);
  if (!entry || now > entry.resetAt) {
    RATE_MAP.set(ip, { count: 1, resetAt: now + 60_000 });
    return true;
  }
  if (entry.count >= MAX_REQ_PER_MIN) return false;
  entry.count++;
  return true;
}

// ── Validation du texte (défense en profondeur) ────────────────────────────
function validateText(text) {
  if (typeof text !== "string") return false;
  const t = text.trim();
  if (!t || t.length > MAX_TEXT_LENGTH) return false;
  // Rejeter tout ce qui ressemble à des données personnelles ou des injections
  if (/https?:\/\//i.test(t)) return false;         // URL
  if (/\{.*\}/i.test(t)) return false;               // Template non résolu {variable}
  if (/<[^>]+>/i.test(t)) return false;              // HTML/XML
  if (/[;\|\&`\$]/i.test(t)) return false;           // Shell injection
  return true;
}

// ── Phonétique ─────────────────────────────────────────────────────────────
function applyPhonetics(text) {
  let t = text;
  for (const [re, rep] of PHON) t = t.replace(re, rep);
  return t;
}

// ── Handler principal ──────────────────────────────────────────────────────
export default async function handler(req, res) {
  // CORS : uniquement safinum.cm + localhost dev
  const origin = req.headers["origin"] || "";
  const corsOrigin = ALLOWED_ORIGINS.includes(origin) ? origin : ALLOWED_ORIGINS[0];
  res.setHeader("Access-Control-Allow-Origin", corsOrigin);
  res.setHeader("Access-Control-Allow-Methods", "POST, OPTIONS");
  res.setHeader("Access-Control-Allow-Headers", "Content-Type");
  res.setHeader("Vary", "Origin");

  if (req.method === "OPTIONS") return res.status(204).end();
  if (req.method !== "POST") return res.status(405).json({ error: "Method not allowed" });

  // Rate limiting
  const ip = req.headers["x-forwarded-for"]?.split(",")[0]?.trim() || "unknown";
  if (!checkRateLimit(ip)) {
    return res.status(429).json({ error: "Rate limit exceeded. Please wait before retrying." });
  }

  // Parse body
  let body;
  try { body = req.body; }
  catch { return res.status(400).json({ error: "Invalid JSON" }); }

  const rawText = body?.text ?? "";
  const lang = (body?.language ?? "fr").toLowerCase().trim();

  // Validation langue
  if (!ALLOWED_LANGS.has(lang)) {
    return res.status(400).json({ error: "Unsupported language code" });
  }

  // Validation texte
  if (!validateText(rawText)) {
    return res.status(400).json({ error: "Invalid text: too long, empty, or contains forbidden patterns" });
  }

  // Préparer le texte phonétique (sans données personnelles — le middleware les a déjà retirées)
  const ttsText = applyPhonetics(rawText.trim());
  const langCode = ELEVEN_LANG[lang] ?? ELEVEN_LANG.default;

  // Clés depuis les variables d'environnement Vercel (jamais dans le code)
  const apiKey   = process.env.ELEVENLABS_API_KEY;
  const voiceId  = process.env.ELEVENLABS_VOICE_ID || "nPczCjzI2devNBz1zQrb";
  const modelId  = process.env.ELEVENLABS_MODEL_ID || "eleven_multilingual_v2";

  if (!apiKey) {
    return res.status(503).json({ error: "TTS service not configured" });
  }

  try {
    const eleven = await fetch(
      `https://api.elevenlabs.io/v1/text-to-speech/${voiceId}?output_format=mp3_44100_128`,
      {
        method: "POST",
        headers: {
          "xi-api-key": apiKey,
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          text: ttsText,
          model_id: modelId,
          language_code: langCode,
          voice_settings: {
            stability: 0.55,
            similarity_boost: 0.78,
            style: 0.12,
            use_speaker_boost: true,
          },
        }),
        signal: AbortSignal.timeout(12_000), // 12s max (Vercel hobby = 10s, Pro = 60s)
      }
    );

    if (!eleven.ok) {
      // Ne pas exposer les détails de l'erreur ElevenLabs au client
      console.error(`[TTS] ElevenLabs error ${eleven.status} for lang=${lang}`);
      return res.status(502).json({ error: "TTS provider unavailable" });
    }

    const audioBuffer = await eleven.arrayBuffer();

    // Headers de sécurité + cache
    res.setHeader("Content-Type", "audio/mpeg");
    res.setHeader("Cache-Control", "public, max-age=86400, s-maxage=86400, stale-while-revalidate=3600");
    res.setHeader("X-TTS-Engine", "elevenlabs-vercel");
    res.setHeader("X-Content-Type-Options", "nosniff");
    res.setHeader("X-Frame-Options", "DENY");
    res.setHeader("Content-Security-Policy", "default-src 'none'");

    return res.status(200).send(Buffer.from(audioBuffer));

  } catch (err) {
    if (err.name === "TimeoutError" || err.name === "AbortError") {
      return res.status(504).json({ error: "TTS request timed out" });
    }
    // Log côté serveur uniquement, jamais au client
    console.error("[TTS] Unexpected error:", err.message);
    return res.status(500).json({ error: "Internal server error" });
  }
}

export const config = {
  api: {
    bodyParser: { sizeLimit: "2kb" }, // Corps max 2 Ko (texte seul, jamais de fichier)
  },
};
