/**
 * authenticate.ts — Shared YouTube OAuth2 authentication module.
 *
 * Provides a single `authenticate()` function used by all YouTube API scripts:
 *   youtube-upload.ts, upload-captions.ts, fix-thumbnails.ts,
 *   youtube-update-description.ts.
 *
 * Token handling:
 *  1. Load .env and .youtube-token.json.
 *  2. If token is valid (expiry_date exists and not expired), return immediately.
 *  3. If expired or expiry_date is missing, refresh the access token.
 *  4. After refresh, ensure expiry_date is present (compute from expires_in
 *     if Google omits it) and persist to disk.
 *  5. If refresh fails, fall back to interactive browser auth (only when
 *     `allowInteractive` is true — e.g. youtube-upload.ts).
 *
 * Usage:
 *   import { authenticate } from "./authenticate";
 *   const auth = await authenticate();
 *   const youtube = google.youtube({ version: "v3", auth });
 *
 * v1.0  2026-06-09  Initial extraction from 4 separate implementations.
 */

import { google } from "googleapis";
import * as fs from "fs";
import * as path from "path";
import * as dotenv from "dotenv";
import * as http from "http";
import * as open from "open";

// Load .env from the same directory as this script
dotenv.config({ path: path.join(__dirname, ".env") });

const TOKEN_PATH = path.join(__dirname, ".youtube-token.json");

const SCOPES = [
  "https://www.googleapis.com/auth/youtube.upload",
  "https://www.googleapis.com/auth/youtube",
];

interface TokenData {
  access_token?: string;
  refresh_token?: string;
  expiry_date?: number;
  expires_in?: number;
  [key: string]: unknown;
}

export interface AuthResult {
  oauth2Client: any;
  youtube: any;
}

/**
 * Ensure expiry_date exists on credentials. Google sometimes omits it.
 */
function ensureExpiryDate(creds: Record<string, any>): void {
  if (!creds.expiry_date && creds.expires_in) {
    creds.expiry_date = Date.now() + creds.expires_in * 1000;
  }
}

/**
 * Authenticate with YouTube API.
 *
 * @param allowInteractive If true, fall back to browser-based OAuth flow when
 *   token refresh fails. Default: false (scripts that run unattended should
 *   set false and exit on refresh failure).
 */
export async function authenticate(allowInteractive = false): Promise<AuthResult> {
  const clientId = process.env.YOUTUBE_CLIENT_ID || process.env.GOOGLE_CLIENT_ID;
  const clientSecret = process.env.YOUTUBE_CLIENT_SECRET || process.env.GOOGLE_CLIENT_SECRET;
  const redirectUri =
    process.env.YOUTUBE_REDIRECT_URI || "http://localhost:3333/oauth2callback";

  if (!clientId || !clientSecret) {
    console.error(
      "Error: Missing YOUTUBE_CLIENT_ID or YOUTUBE_CLIENT_SECRET in .env"
    );
    process.exit(1);
  }

  const oauth2Client = new google.auth.OAuth2(
    clientId,
    clientSecret,
    redirectUri
  );

  // No token file at all
  if (!fs.existsSync(TOKEN_PATH)) {
    if (allowInteractive) {
      return interactiveAuth(oauth2Client);
    }
    console.error("Error: .youtube-token.json not found. Run youtube-upload.ts first.");
    process.exit(1);
  }

  const tokenData: TokenData = JSON.parse(
    fs.readFileSync(TOKEN_PATH, "utf-8")
  );
  oauth2Client.setCredentials(tokenData);

  // Token is still valid
  if (tokenData.expiry_date && tokenData.expiry_date > Date.now()) {
    const youtube = google.youtube({ version: "v3", auth: oauth2Client });
    return { oauth2Client, youtube };
  }

  // Token expired or missing expiry_date — try refresh
  if (tokenData.refresh_token) {
    try {
      const { credentials } = await oauth2Client.refreshAccessToken();
      const creds = credentials as Record<string, any>;
      ensureExpiryDate(creds);
      oauth2Client.setCredentials(credentials);
      fs.writeFileSync(TOKEN_PATH, JSON.stringify(credentials, null, 2));
      console.log("Token refreshed successfully");
      const youtube = google.youtube({ version: "v3", auth: oauth2Client });
      return { oauth2Client, youtube };
    } catch (err) {
      console.error("Token refresh failed:", err);
      if (!allowInteractive) {
        process.exit(1);
      }
      console.log("Falling back to interactive auth...");
    }
  }

  // Interactive auth
  if (allowInteractive) {
    return interactiveAuth(oauth2Client);
  }

  console.error("Error: No refresh_token available. Run youtube-upload.ts to re-authenticate.");
  process.exit(1);
}

async function interactiveAuth(oauth2Client: any): Promise<AuthResult> {
  return new Promise((resolve, reject) => {
    const authUrl = oauth2Client.generateAuthUrl({
      access_type: "offline",
      scope: SCOPES,
      prompt: "consent",
    });

    console.log("\n=== YouTube Authentication ===");
    console.log("Opening browser for authentication...\n");
    console.log("Auth URL:", authUrl, "\n");

    const server = http.createServer(async (req, res) => {
      try {
        const urlObj = new URL(req.url || "", "http://localhost:3333");
        if (urlObj.pathname === "/oauth2callback") {
          const code = urlObj.searchParams.get("code");
          if (code) {
            const { tokens } = await oauth2Client.getToken(code);
            oauth2Client.setCredentials(tokens);
            fs.writeFileSync(TOKEN_PATH, JSON.stringify(tokens, null, 2));

            res.writeHead(200, { "Content-Type": "text/html" });
            res.end(
              `<html><body style="font-family:sans-serif;text-align:center;padding:50px">
                <h1>Authentication Successful!</h1>
                <p>You can close this window.</p></body></html>`
            );

            server.close();
            const youtube = google.youtube({ version: "v3", auth: oauth2Client });
            resolve({ oauth2Client, youtube });
          }
        }
      } catch (err) {
        reject(err);
      }
    });

    server.listen(3333, () => {
      open(authUrl).catch(() => {
        console.log("Could not open browser. Visit the URL above manually.");
      });
    });

    setTimeout(() => {
      server.close();
      reject(new Error("Authentication timed out after 5 minutes"));
    }, 5 * 60 * 1000);
  });
}
