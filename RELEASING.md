# Releasing shaapi

Publishing is automated via GitHub Actions + **PyPI Trusted Publishing** (OIDC).
No API tokens to create, store or rotate.

## One-time setup (do this once)

1. **Register the trusted publisher on PyPI**
   Go to https://pypi.org/manage/project/shaapi/settings/publishing/ and add a
   *GitHub* publisher with exactly:
   - **Owner:** `Shalom-302`
   - **Repository name:** `shaapi`
   - **Workflow name:** `publish.yml`
   - **Environment name:** `pypi`

2. **(Recommended) Create the `pypi` environment in GitHub**
   Repo → *Settings* → *Environments* → *New environment* → name it `pypi`.
   You can add a required reviewer here to gate releases.

That's it — the workflow [`/.github/workflows/publish.yml`](.github/workflows/publish.yml)
authenticates to PyPI through OIDC, no secrets involved.

## Cutting a release

1. Bump the version in [`pyproject.toml`](pyproject.toml) (`version = "x.y.z"`).
2. Commit and push to `main`.
3. Create a GitHub Release with a tag (e.g. `v0.1.3`):
   ```bash
   gh release create v0.1.3 --title "v0.1.3" --notes "What changed…"
   ```
   (or use the GitHub UI → *Releases* → *Draft a new release*).
4. The **Publish to PyPI** workflow runs automatically: it builds with `uv` and
   publishes the wheel + sdist to https://pypi.org/project/shaapi/.

You can also trigger it manually from the *Actions* tab (*workflow_dispatch*).

## Versioning

shaapi follows [Semantic Versioning](https://semver.org): `MAJOR.MINOR.PATCH`.
Each PyPI version is immutable — never reuse a version number.
