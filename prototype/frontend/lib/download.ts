// Single source of truth for the Windows .exe download.
// Set via env (see .env.example) when a GitHub Release is published.
// Falls back to the Releases page so the button always points somewhere real.

export const EXE_URL = process.env.NEXT_PUBLIC_EXE_URL ?? "";
export const EXE_VERSION = process.env.NEXT_PUBLIC_EXE_VERSION ?? "";
export const EXE_SIZE = process.env.NEXT_PUBLIC_EXE_SIZE ?? "";
export const EXE_SHA256 = process.env.NEXT_PUBLIC_EXE_SHA256 ?? "";
export const RELEASE_URL = process.env.NEXT_PUBLIC_RELEASE_URL ?? "";

/** Clearly-identifiable placeholder until a release is published. */
export const PLACEHOLDER_URL =
  "https://github.com/akshanshuwu/signit_prototype/releases";

/** Always safe to link: direct .exe → release page → placeholder. */
export const DOWNLOAD_URL = EXE_URL || RELEASE_URL || PLACEHOLDER_URL;

/** True only when a direct .exe file URL is configured. */
export const HAS_DIRECT_DOWNLOAD = EXE_URL !== "";
