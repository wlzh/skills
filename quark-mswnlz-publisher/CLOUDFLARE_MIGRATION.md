# Resource-site Cloudflare account migration

Target account: `kingcolixhs@gmail.com` / `ff9ae38b2050743cef380268109348c6`.
Project: `doc869hr`; actual assigned hostname: `doc869hr-6r4.pages.dev`.
Production hostname remains `doc.869hr.uk`.

The old Pages project belongs to `cba95940715cce032368055d71c9f548`
and serves `doc869hr.pages.dev`. Keep it until production cutover is verified
and the observation window has passed. DNS remains in the old account.

## Credentials and deployment

- Dedicated credentials are stored outside Git in
  `~/.config/doc869hr/cloudflare.env` (directory 0700, file 0600).
- The token has Cloudflare Pages Edit permission on the target account only.
- Do not replace the shared Wrangler OAuth login used by other sites.
- `DOC869HR_CF_ENV` can override the local credential file location.
- The script validates the target account via the Pages API before building.
- Wrangler deploy runs in a temporary directory to avoid old account caches.
- A unique `deployment-release.json` must match on the assigned Pages host
  and production hostname before channel or resource notifications are sent.
- Deploy errors propagate to the caller. A failed publish must not be retried
  by repeating netdisk transfers; retry only the site deployment step.

## Cutover checklist

1. Validate and deploy the existing build to the target project.
2. Record the old project, custom-domain status, DNS content, TTL and proxy mode.
3. Verify target Pages routes before releasing the old custom-domain binding.
4. Associate `doc.869hr.uk` with the target project and change its DNS CNAME
   to the actual assigned target, not the project-name-derived hostname.
5. Wait for certificate/domain activation, then verify the release marker,
   home, guides, sitemap, resource catalog, category and resource detail routes.
6. Run a complete normal deployment with `SKIP_NOTIFY=1`, including source
   tests, build, output validation and Gitee snapshot.
7. Record live verification evidence before declaring migration complete.

## Verified cutover (2026-10-20)

- CNAME `doc.869hr.uk` now points to `doc869hr-6r4.pages.dev`.
- Proxy remained enabled throughout; TTL remains automatic.
- New custom domain ownership and HTTP validation are both `active`.
- The old custom-domain association was removed; the old Pages project and
  its deployments remain intact. Other old-account services were not changed.
- Release markers match on both hosts. Home, guides, sitemap and catalog probes
  passed. The browser search for `AI` returned resource and archive results.
- Gitee backup `5e8620791490505fbe34d03226ab09cac2df253d` includes the updated guide.
- Python urllib probes received Cloudflare 1010 while curl succeeded. Verification
  now uses curl without weakening zone security; API tokens are passed on stdin.
- This is automatic deployment from the existing publishing pipeline, not a
  new filesystem watcher or GitHub push-triggered build.
- Final full publishing run exited 0 with `SKIP_NOTIFY=1`: deployment
  `4e8f972f-c647-47a7-b190-eaa08c1000b6`, production domain `active`, both release
  markers and public routes verified. No test notifications were sent.
- Validation covered 1,073 resources, 11 categories, 1,142 sitemap URLs and
  1,161 generated pages; 10 new release/failure unit tests passed.

## Rollback

Keep the old project and its build. If cutover fails, remove the target domain
association, restore the old association and recorded DNS settings, then wait
for activation and verify the old public routes. Do not assume DNS reversal
alone immediately restores service. The new deployment script fails closed
while the production hostname serves a different release.
