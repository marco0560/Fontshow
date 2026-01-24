# Decision 0012 - GitHub Pages deployment strategy

Date: 25/01/2026
Status: Accepted

## Context

Fontshow publishes its documentation using GitHub Pages.

Historically, GitHub Pages supported deployment from a `gh-pages` branch.
Modern GitHub Pages supports deployment via GitHub Actions using the
`github-pages` environment.

## Decision

The project uses **GitHub Actions** to deploy documentation.

- Source branch: `main`
- Build performed by CI
- Deployment target: `github-pages` environment
- No `gh-pages` branch is used or maintained

## Consequences

- No manual branch management
- Cleaner Git history
- Reproducible documentation builds
- Compatible with semantic-release and CI workflows

## Rejected alternatives

- Deploying from `gh-pages` branch (legacy, deprecated)
- Manual documentation publishing
