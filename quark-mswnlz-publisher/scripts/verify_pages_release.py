#!/usr/bin/env python3
"""Fail closed unless the intended account and public release match."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import time
import uuid

ACCOUNT = "ff9ae38b2050743cef380268109348c6"
DOMAIN = "doc.869hr.uk"
MARKER = "deployment-release.json"


def fetch(url, token=None):
    # urllib's default client is rejected with Cloudflare 1010 on this site.
    # Keep the zone's security settings intact and use the installed curl client.
    config = 'header = "Cache-Control: no-cache"\n'
    if token:
        config += "header = " + json.dumps("Authorization: Bearer " + token) + "\n"
    result = subprocess.run(
        ["curl", "--fail", "--silent", "--show-error", "--max-time", "30",
         "--config", "-", url],
        input=config.encode(), capture_output=True,
    )
    if result.returncode:
        raise RuntimeError(f"HTTP probe failed for {url}: curl exit {result.returncode}")
    return result.stdout


def project():
    if os.environ.get("CLOUDFLARE_ACCOUNT_ID") != ACCOUNT:
        raise RuntimeError("Unexpected Cloudflare account")
    token = os.environ.get("CLOUDFLARE_API_TOKEN")
    if not token:
        raise RuntimeError("Missing project API token")
    name = os.environ.get("CF_PAGES_PROJECT", "doc869hr")
    data = json.loads(fetch(
        f"https://api.cloudflare.com/client/v4/accounts/{ACCOUNT}/pages/projects/{name}",
        token,
    ))
    if not data.get("success"):
        raise RuntimeError("Cloudflare project lookup failed")
    result = data["result"]
    if result["name"] != name:
        raise RuntimeError("Unexpected Pages project")
    return result


def main():
    parser = argparse.ArgumentParser()
    actions = parser.add_mutually_exclusive_group(required=True)
    actions.add_argument("--preflight", action="store_true")
    actions.add_argument("--stamp", type=Path)
    actions.add_argument("--verify", type=Path)
    args = parser.parse_args()
    if args.stamp:
        (args.stamp / MARKER).write_text(
            json.dumps({"release": uuid.uuid4().hex, "account": ACCOUNT}) + "\n",
            encoding="utf-8",
        )
        return
    info = project()
    print(f"Confirmed Pages target: {ACCOUNT}/{info['name']} ({info['subdomain']})")
    if args.preflight:
        return
    if DOMAIN not in info.get("domains", []):
        raise RuntimeError("Production domain is not bound to the new project")
    expected = (args.verify / MARKER).read_bytes()
    for attempt in range(6):
        try:
            for host in (info["subdomain"], DOMAIN):
                actual = fetch(f"https://{host}/{MARKER}?release={json.loads(expected)['release']}")
                if actual != expected:
                    raise RuntimeError(f"Release mismatch on {host}")
            for path in ("/", "/guides/", "/sitemap.xml", "/resource-catalog.json"):
                if not fetch(f"https://{DOMAIN}{path}"):
                    raise RuntimeError(f"Empty response: {path}")
            print("Production release marker and public routes verified.")
            return
        except Exception as error:
            if attempt == 5:
                raise RuntimeError("Production verification failed; do not notify") from error
            print(f"Waiting for production release ({attempt + 1}/6)")
            time.sleep(10)


if __name__ == "__main__":
    main()
