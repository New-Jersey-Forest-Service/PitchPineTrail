# To Run Local:

Start-Process -FilePath 'C:\Users\wzipse\AppData\Local\anaconda3\python.exe' -ArgumentList @('-m','http.server','8001') -WindowStyle Hidden

# GitHub Pages Site Instructions

These instructions explain how to publish the Pitch Pine Trail web port on GitHub Pages.

## Current Repo Layout

The browser app currently lives in:

```text
web/
├── index.html
├── css/style.css
└── js/
    ├── game.js
    ├── screens.js
    ├── sounds.js
    └── charts.js
```

The web app references shared image and audio assets in:

```text
src/assets/
```

The current browser asset paths use this pattern:

```text
../src/assets/filename.jpg
../src/assets/filename.wav
```

That means the app works when the repository root is served and the user opens `/web/`.

Example local test URL:

```text
http://localhost:8001/web/
```

It does not work when `web/` is served as the document root, because `../src/assets/...` cannot climb outside the published site root.

## Important GitHub Pages Constraint

GitHub Pages "Deploy from a branch" supports publishing from either:

- the root of a selected branch, or
- the `/docs` folder of a selected branch.

Do not assume GitHub Pages can publish directly from `/web` using the branch/folder dropdown.

Official GitHub docs:

- Creating a GitHub Pages site: https://docs.github.com/en/pages/getting-started-with-github-pages/creating-a-github-pages-site
- Configuring a publishing source: https://docs.github.com/en/pages/getting-started-with-github-pages/configuring-a-publishing-source-for-your-github-pages-site

## Recommended Deployment Option

Recommended for the current repo: publish from the repository root and keep the app at `/web/`.

This preserves the current shared asset paths without duplicating the large `src/assets/` folder.

Expected public URL:

```text
https://new-jersey-forest-service.github.io/PitchPineTrail/web/
```

Steps:

1. Make sure the web files are committed to the branch you want to publish, usually `main`.
2. Make sure `web/index.html` exists.
3. Make sure `src/assets/` is present on the same branch.
4. On GitHub, open the repository.
5. Go to `Settings`.
6. In the left sidebar, go to `Pages`.
7. Under `Build and deployment`, set `Source` to `Deploy from a branch`.
8. Select the branch, usually `main`.
9. Select the folder `/(root)`.
10. Click `Save`.
11. Wait for the Pages workflow to finish.
12. Visit:

```text
https://new-jersey-forest-service.github.io/PitchPineTrail/web/
```

Note: If visitors go to the repository root URL without `/web/`, they will see the root-level `README.md`/default Pages behavior or a non-game page unless a redirect or root `index.html` is added.

## Optional Root Redirect

If the repository root is published and you want the shorter URL to open the game, add a root-level `index.html` that redirects to `web/`.

Example:

```html
<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <meta http-equiv="refresh" content="0; url=web/">
    <title>Pitch Pine Trail</title>
  </head>
  <body>
    <p><a href="web/">Open Pitch Pine Trail</a></p>
  </body>
</html>
```

Only add this if the team is comfortable changing the repository root web entry behavior.

## Alternative Option: Move Web App To `/docs`

If the team wants GitHub Pages to serve the game from the project root URL:

```text
https://new-jersey-forest-service.github.io/PitchPineTrail/
```

then move or build the web app into `/docs`, because GitHub Pages branch publishing supports `/docs`.

However, this requires resolving asset paths. Options:

- Copy `src/assets/` into `docs/assets/` and update all web paths to `assets/filename`.
- Add a build script that copies `web/` and required assets into `docs/`.
- Keep `src/assets/` shared and use a custom GitHub Actions workflow that uploads an artifact containing both the web app and assets in the correct relative structure.

Do not simply move `web/index.html` into `/docs` without updating asset paths.

## Alternative Option: GitHub Actions Deployment

Use GitHub Actions if the team wants a custom publish artifact.

This is useful if you want to:

- keep source files in `web/`,
- copy `src/assets/` during deployment,
- publish the artifact root as the game root,
- avoid committing duplicated assets.

High-level workflow:

1. Configure Pages source to `GitHub Actions`.
2. Add a workflow under `.github/workflows/`.
3. Check out the repository.
4. Create a temporary publish folder.
5. Copy `web/*` into that folder.
6. Copy `src/assets/` into a location matching the app's asset paths, or rewrite paths during the build.
7. Upload the publish folder using `actions/upload-pages-artifact`.
8. Deploy using `actions/deploy-pages`.

If this route is chosen, update this file with the exact workflow and local test command.

## Local Testing Before Publishing

Use the documented local Anaconda Python interpreter:

```powershell
Start-Process -FilePath 'C:\Users\wzipse\AppData\Local\anaconda3\python.exe' -ArgumentList @('-m','http.server','8001') -WindowStyle Hidden
```

Open:

```text
http://localhost:8001/web/
```

Verify:

- intro screen loads,
- Begin button runs the zoom flow,
- main game screen loads with metrics and buttons,
- at least one turn can be played,
- shared JPG backgrounds load,
- WAV sounds are triggered after click interaction,
- analysis lab opens,
- Chart.js loads from CDN,
- html2canvas loads from CDN for certificate saving.

At the end of testing, ask the user whether they want the local test server shut down. If yes, stop only the testing server process that was started for this repo.

## Publishing Checklist

Before enabling or updating GitHub Pages:

1. Confirm the intended public URL:
   - `/PitchPineTrail/web/` for root publishing, or
   - `/PitchPineTrail/` for a custom `/docs` or Actions artifact setup.
2. Confirm asset paths in browser dev tools.
3. Confirm `src/assets/` files are committed if using root publishing.
4. Confirm CDN access is acceptable for Chart.js and html2canvas.
5. Confirm there is no sensitive data in the repository, since GitHub Pages sites are publicly available.
6. Push the chosen branch.
7. Configure Pages in repository settings.
8. Wait for the Pages workflow to complete.
9. Visit the published URL and test a complete gameplay path.

## Troubleshooting

If the game page loads but backgrounds are missing:

- Check whether the site was published from `/web` or another folder.
- Open browser dev tools and inspect failed asset URLs.
- If failed URLs contain `/src/assets/...`, make sure `src/assets/` is included in the published site root.

If JavaScript modules fail to load:

- Make sure the site is loaded via `https://` or `http://`, not by opening `index.html` directly from the filesystem.
- Check browser console errors.

If Chart.js or html2canvas fail:

- Confirm the browser can reach the CDN URLs in `web/index.html`.
- If the deployment environment should avoid CDN dependencies, vendor these libraries locally and update `web/index.html`.

If changes do not appear immediately:

- Wait several minutes for GitHub Pages deployment.
- Check the repository `Actions` tab for the Pages workflow status.
- Hard refresh the browser.
