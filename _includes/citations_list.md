{%- assign data_key       = include.data | default: "citations" -%}
{%- assign style          = include.style | downcase | default: "apa" -%}
{%- assign group_by_year  = include.group_by_year | default: true -%}
{%- assign limit          = include.limit | default: 999999 -%}

{%- assign pubs = site.data[data_key] | sort: "Year" | reverse -%}

{%- assign venues         = include.venue | downcase | split: ";" -%}
{%- assign venues_exclude = include.venue_exclude | downcase | split: ";" -%}
{%- assign years          = include.year | split: ";" -%}
{%- assign title_terms    = include.title_search | downcase | split: ";" -%}
{%- assign venue_terms    = include.venue_search | downcase | split: ";" -%}
{%- assign venue_terms_x  = include.venue_search_exclude | downcase | split: ";" -%}
{%- assign author_terms   = include.author | downcase | split: ";" -%}

{%- assign count = 0 -%}
{%- assign last_year = "" -%}

{%- for citation in pubs -%}
  {%- assign title = citation.Title | default: citation.title | default: "" -%}
  {%- assign year  = citation.Year  | default: citation.year  | default: "" -%}
  {%- assign venue = citation.Publication | default: citation.Venue | default: citation.Outlet | default: "" -%}
  {%- assign url   = citation.URL | default: citation.Url | default: "" -%}
  {%- assign pdf   = citation.PDF | default: citation.Pdf | default: "" -%}
  {%- assign doi   = citation.DOI | default: citation.Doi | default: "" -%}
  {%- assign code  = citation.Code | default: citation.GitHub | default: "" -%}
  {%- assign bibf  = citation.BibTeX | default: citation.Bibtex | default: "" -%}

  {%- assign authors_cell = "" -%}
  {%- if include.authors_col -%}{%- assign authors_cell = citation[include.authors_col] | default: "" -%}{%- endif -%}
  {%- if authors_cell == "" -%}{%- assign authors_cell = citation.Authors | default: citation.Author | default: citation["Author(s)"] | default: "" -%}{%- endif -%}
  {%- if authors_cell == "" -%}
    {%- for kv in citation -%}{%- assign k = kv[0] | downcase -%}{%- if k contains "author" -%}{%- assign authors_cell = kv[1] -%}{%- break -%}{%- endif -%}{%- endfor -%}
  {%- endif -%}

  {%- assign title_l = title | downcase -%}
  {%- assign venue_l = venue | downcase -%}
  {%- assign authors_l = authors_cell | downcase -%}

  {%- assign ok = true -%}
  {%- if include.venue and venues != empty -%}{%- assign ok = venues contains venue_l -%}{%- endif -%}
  {%- if ok and include.venue_exclude and venues_exclude != empty -%}{%- if venues_exclude contains venue_l -%}{%- assign ok = false -%}{%- endif -%}{%- endif -%}
  {%- if ok and include.year and years != empty -%}{%- assign ok = years contains year -%}{%- endif -%}
  {%- if ok and include.title_search and title_terms != empty -%}
    {%- assign matched = false -%}
    {%- for term in title_terms -%}{%- if term != "" and title_l contains term -%}{%- assign matched = true -%}{%- endif -%}{%- endfor -%}
    {%- assign ok = matched -%}
  {%- endif -%}
  {%- if ok and include.venue_search and venue_terms != empty -%}
    {%- assign matched = false -%}
    {%- for term in venue_terms -%}{%- if term != "" and venue_l contains term -%}{%- assign matched = true -%}{%- endif -%}{%- endfor -%}
    {%- assign ok = matched -%}
  {%- endif -%}
  {%- if ok and include.venue_search_exclude and venue_terms_x != empty -%}
    {%- for term in venue_terms_x -%}{%- if term != "" and venue_l contains term -%}{%- assign ok = false -%}{%- endif -%}{%- endfor -%}
  {%- endif -%}
  {%- if ok and include.author and author_terms != empty -%}
    {%- assign matched = false -%}
    {%- for term in author_terms -%}{%- if term != "" and authors_l contains term -%}{%- assign matched = true -%}{%- endif -%}{%- endfor -%}
    {%- assign ok = matched -%}
  {%- endif -%}
  {%- unless ok -%}{%- continue -%}{%- endunless -%}

  {% if group_by_year and last_year != year %}
  <h2 class="pub-year">{{ year }}</h2>
  {% assign last_year = year %}
  {% endif %}

  {%- assign names = authors_cell
      | replace: " and ", ";"
      | replace: ", and ", ";"
      | replace: "|", ";"
      | split: ";"
  -%}
  {%- assign formatted = "" -%}
  {%- assign printed = 0 -%}
  {%- for n in names -%}
    {%- assign n_trim = n | strip -%}
    {%- if n_trim == "" -%}{%- continue -%}{%- endif -%}
    {%- assign printed = printed | plus: 1 -%}
    {%- if n_trim contains "," -%}
      {%- assign last = n_trim | split: "," | first | strip -%}
      {%- assign first = n_trim | split: "," | last  | strip -%}
    {%- else -%}
      {%- assign parts = n_trim | split: " " -%}
      {%- assign last = parts | last -%}
      {%- assign first = n_trim | remove: last | strip -%}
    {%- endif -%}

    {%- if style == "mla" or style == "chicago" -%}
      {%- assign name_fmt = last | append: ", " | append: first -%}
    {%- elsif style == "vancouver" -%}
      {%- assign initial = first | slice: 0, 1 -%}
      {%- assign name_fmt = last | append: " " | append: initial -%}
    {%- else -%} {%- comment -%} apa/harvard default {%- endcomment -%}
      {%- assign initial = first | slice: 0, 1 -%}
      {%- assign name_fmt = last | append: ", " | append: initial | append: "." -%}
    {%- endif -%}

    {%- assign formatted = formatted | append: name_fmt -%}
    {%- unless forloop.last -%}{%- assign formatted = formatted | append: "; " -%}{%- endunless -%}
  {%- endfor -%}
  {%- if printed == 0 -%}{%- assign formatted = authors_cell | strip -%}{%- endif -%}

  {%- comment -%} Always link title to Google Scholar search for the title {%- endcomment -%}
  {%- assign gs_url = title | cgi_escape | prepend: "https://scholar.google.com/scholar?q=" -%}

  {{ formatted }}{% if year != "" %} ({{ year }}){% endif %}.
  **{% if title != "" %}<a href="{{ gs_url }}">{{ title }}</a>{% else %}(untitled){% endif %}**.{% if venue != "" %} _{{ venue }}_{% endif %}<br>

  {%- comment -%} Show resource badges only if present in CSV {%- endcomment -%}
  {%- assign any_links = false -%}
  {%- if url != "" -%}{%- assign any_links = true -%}[URL]({{ url }}){%- endif -%}
  {%- if pdf != "" -%}{%- if any_links -%} · {%- endif -%}{%- assign any_links = true -%}[PDF]({{ pdf }}){%- endif -%}
  {%- if doi != "" -%}{%- if any_links -%} · {%- endif -%}{%- assign any_links = true -%}[DOI](https://doi.org/{{ doi }}){%- endif -%}
  {%- if code != "" -%}{%- if any_links -%} · {%- endif -%}{%- assign any_links = true -%}[Code/Project]({{ code }}){%- endif -%}
  {%- if bibf != "" -%}{%- if any_links -%} · {%- endif -%}[BibTeX]({{ bibf }}){%- endif -%}
  <br>

  {%- assign count = count | plus: 1 -%}
  {%- if count >= limit -%}{%- break -%}{%- endif -%}
{%- endfor -%}
