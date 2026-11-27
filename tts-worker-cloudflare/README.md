# Safinum TTS Worker — Cloudflare Workers

Proxy ElevenLabs hébergé sur Cloudflare Workers (edge mondial, 0 cold start, gratuit).

## Déploiement en 4 commandes

```bash
npm install -g wrangler
wrangler login
wrangler secret put ELEVENLABS_API_KEY     # coller sk_c79053c7...
wrangler secret put ELEVENLABS_VOICE_ID    # nPczCjzI2devNBz1zQrb
wrangler deploy
```

Le Worker est en ligne à `https://safinum-tts.<ton-sous-domaine>.workers.dev`

## Endpoint

```
POST https://safinum-tts.<sous-domaine>.workers.dev/api/audio/tts
Content-Type: application/json

{ "text": "Mbolô, bâ wôm nde i lon", "language": "ewo" }
```

Retourne `audio/mpeg` (MP3 128kbps, ~40 Ko pour 5 s).

## Mettre à jour voice_bridge.js

Remplacer dans `TTS_ENDPOINTS` :
```js
const TTS_ENDPOINTS = [
  "https://safinum-tts.<sous-domaine>.workers.dev/api/audio/tts",   // Cloudflare (primaire)
  "https://maryellen-parchable-gertude.ngrok-free.dev/api/audio/tts",  // ngrok (backup)
  "http://127.0.0.1:3000/api/audio/tts",                              // local (backup)
];
```

## Cache KV (optionnel — gain supplémentaire)

```bash
wrangler kv:namespace create TTS_CACHE
# Copier l'id retourné dans wrangler.toml (décommenter les lignes kv_namespaces)
wrangler deploy
```

Avec KV : même texte déjà synthétisé → retourné en < 50 ms depuis le cache edge.
