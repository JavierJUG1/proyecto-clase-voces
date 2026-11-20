import { ElevenLabsClient } from "@elevenlabs/elevenlabs-js";

// Reads ELEVENLABS_API_KEY from the environment (loaded from .env.local via `node --env-file=.env.local`).
export const elevenlabs = new ElevenLabsClient();
