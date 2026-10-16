# Screenshots and media

The public visual set uses synthetic or de-identified content. The current
README screenshot is the SANO-X2 document workspace capture at
`docs/assets/sano-x2/documents-1440.webp`; it is a static reviewer visual, not
evidence of a live provider response.

The README also links the existing promo cover at
`docs/assets/sano-promo/sano-promo-t056.250.png` and the 60-second video on the
`media/sano-promo-video` branch. The video is an existing repository artifact;
capture work does not require downloading or replaying it. X1 responsive
captures remain documented in [SANO-X1 validation](sano-x1-validation.md).

## Current local capture path

Use the isolated Python 3.12 environment and local server:

```powershell
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

Review the authenticated product surfaces with synthetic fixtures only:

- `http://127.0.0.1:8000/workspace`
- `http://127.0.0.1:8000/family-access`
- `http://127.0.0.1:8000/genetics`
- `http://127.0.0.1:8000/demo/health-vault`

The `/demo/health-vault` surface is read-only. The authenticated workspace
surfaces require the normal local bootstrap and authorization flow. Do not use
production deployments, real documents, real genetic files, or live provider
requests for screenshot capture.

## Safe capture guidance

1. Start the local server from the repository root and use a stable viewport.
2. Use only the committed synthetic/demo fixtures or freshly generated
   synthetic values. Keep source provenance and safety labels visible where
   they are part of the reviewer behavior.
3. Capture the page content without a desktop, private browser profile,
   address-bar secrets, local filesystem paths, or unrelated notifications.
4. Inspect the image before saving it. Reject any real patient, family,
   genetic, credential, token, API-key, private URL, or provider-response
   content.
5. Save only approved public visuals under `docs/assets/`. Update this guide
   and the relevant validation document when a new capture replaces a current
   one; do not add historical screenshot dumps or an `docs/archive` folder.

## Public asset references

- [README](../README.md) — current X2 screenshot and promo media.
- [SANO-X1 validation](sano-x1-validation.md) — responsive X1 visual set.
- [Documentation index](README.md) — navigation to current product and
  validation documents.

Screenshots are supporting reviewer evidence. They do not establish clinical
validation, medical correctness, provider availability, or production
security.
