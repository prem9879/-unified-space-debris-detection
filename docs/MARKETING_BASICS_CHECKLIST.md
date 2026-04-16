# Marketing Basics Checklist

This project now includes baseline SEO endpoints:
- `/robots.txt`
- `/sitemap.xml`
- `<meta name="description">` and robot directives on the landing page.

## Manual Search Engine Submission Steps

1. Google Search Console
- Open https://search.google.com/search-console
- Add your deployed domain as a property.
- Verify ownership (DNS TXT preferred).
- Submit `https://<your-domain>/sitemap.xml`.
- Request indexing for key pages (`/`, `/privacy-policy`, `/terms-of-service`, `/signup`, `/login`).

2. Bing Webmaster Tools
- Open https://www.bing.com/webmasters
- Add and verify the same domain.
- Submit sitemap URL.

3. Yandex Webmaster (optional)
- Open https://webmaster.yandex.com
- Add site, verify ownership, submit sitemap.

## Tracking Validation

1. Open the app and confirm page visits create records in `app_events`.
2. Accept/decline cookie consent and verify `cookie_consent_updated` events.
3. Trigger CTA buttons and verify `cta_click` events.
4. Check that events remain off when consent is declined.
