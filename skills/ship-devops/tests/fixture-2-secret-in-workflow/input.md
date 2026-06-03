# Synthetic Input for Fixture 2: Secret literal in workflow YAML

You are reviewing the following file. Apply the `ship-devops` rubric.

## File: `.github/workflows/publish.yml`

```yaml
name: publish
on:
  push:
    tags: ['v*.*.*']

jobs:
  publish:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@b4ffde65f46336ab88eb53be808477a3936bae11 # v4.1.1
      - uses: actions/setup-node@b39b52d1213e96004bfcb1c61a8a6fa8ab84f3e8 # v4.0.1
        with:
          node-version-file: .nvmrc
          cache: 'npm'
          registry-url: https://registry.npmjs.org
      - run: npm ci
      - run: npm run build
      - run: npm test
      - run: npm publish
        env:
          NODE_AUTH_TOKEN: npm_FAKEnpm_pUbL1sH_t0KeN_dO_n0T_uS3
          STRIPE_KEY: sk_live_FakeBuTReal-lookingStripeKey
```

---

Apply the ship-devops rubric and produce a structured review.
