# sa1ntsinner.github.io

My personal page: https://sa1ntsinner.github.io

Plain HTML, CSS and JavaScript in `site/`. No dependencies or build step.

Serve locally with `python -m http.server 8080 --directory site`.

The activity squares read one JSON snapshot, `site/data/activity.json`: a shade
per day from my GitHub calendar, no counts. It is collected and published
privately from my computer; this repository has no credentials, scripts or workflows.

Publishing uses the `gh-pages` branch as a static Pages source. The source in
`site/` also includes the Sift page at `/sift/`.
