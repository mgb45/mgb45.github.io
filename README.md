# mgb45.github.io

## Keeping publications up to date

`_data/citations.csv` powers the Publications page (`pages/publications.md` via
`_includes/citations_list.md`) and is kept in sync with Google Scholar
automatically by the `.github/workflows/update-citations.yml` workflow,
instead of manually re-exporting a CSV from Scholar.

- The workflow runs weekly (and can be triggered manually from the Actions
  tab) and opens a pull request with any updates for review.
- It relies on the repository variable `SCHOLAR_ID`, set to the `user=`
  value from the Google Scholar profile URL
  (`https://scholar.google.com/citations?user=<SCHOLAR_ID>`).
  If the variable is not set, the workflow uses Michael Burke's public profile
  (`Abz56f4AAAAJ`) by default.
- `scripts/update_citations.py` merges new Scholar data into the CSV by
  matching publications on a normalized title. Scholar-derived fields
  (Authors, Publication, Volume, Number, Pages, Year, Publisher) are refreshed
  automatically when Scholar returns a non-empty value, while manually curated
  fields (DOI, PDF, Code, URL and BibTeX) are always preserved.
- Google Scholar has no official API and scraping (via the `scholarly`
  package) is best-effort; if it becomes unreliable, the fetch step in
  `scripts/update_citations.py` can be swapped for a paid service such as
  SerpApi's Google Scholar Author API without changing the CSV merge logic.