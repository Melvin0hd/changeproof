# Official references checked 22 October 2026

The [hackathon rules](https://nebiusglobalaihackathon.devpost.com/rules) list the
Best Apps and Agents Track, public licensed source, a working demo/test build,
English materials, technology feedback and a public YouTube video under three
minutes. Submission closes 30 October at 10:00 PDT. Free judge access must remain
available through the judging period ending 15 December. Eligibility, rights and
team representation still require owner confirmation.

The [official FAQ](https://nebiusglobalaihackathon.devpost.com/details/faqs)
explains that NVIDIA inference through Token Factory can meet the platform
requirement without hosting the rest of the application on AI Cloud. This does
not certify this entry or waive any other requirement.

[GitHub's Pages workflow documentation](https://docs.github.com/en/pages/getting-started-with-github-pages/using-custom-workflows-with-github-pages)
describes artifact upload, `github-pages`, and deployment permissions. P1 prepares
that route for a static-only site, separate from the local Python provider path.

[GitHub Actions billing](https://docs.github.com/en/billing/concepts/product-billing/github-actions)
states standard hosted runners for public repositories are free. These workflows
are manual-only, restricted to the intended public repository/main branch and
standard Ubuntu runners. No private/larger runner or paid provider is enabled.

Action major tags were resolved read-only to their actual official repository
commit IDs. Both workflow files use pinned SHAs. Their JSON-form YAML is parsed
as structured data by the dependency-free release tests. No GitHub workflow has
executed yet; syntax/policy checks are not a claim of a real runner PASS.
