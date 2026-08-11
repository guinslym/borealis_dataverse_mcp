# Example questions

Questions a researcher or data librarian can ask an MCP host connected to this toolkit, written for Statistics Canada and Health Canada survey holdings in Borealis.

Every match count below was measured against the live Borealis API. Counts drift as deposits change; treat them as an indication of precision, not as fixed values.

## Quote the survey title

Borealis combines bare terms with `OR`, so an unquoted multi-word title matches thousands of unrelated records. Quoting the title searches it as a phrase.

| Query | Matches | Top result |
| --- | --- | --- |
| `Canadian Community Health Survey` | 16882 | Community Health Programs Directory |
| `"Canadian Community Health Survey"` | 106 | Canadian Community Health Survey |
| `Labour Force Survey` | 12463 | Canadians' Understanding of Issues Related to the Aging Population |
| `"Labour Force Survey"` | 2084 | Labour Force Survey |

Three related rules:

- Acronyms work as phrases: `"PCCF+"`, `"SPSD/M"`, `"CCHS"`, `"PIAAC"`.
- Match the title Borealis actually stores. `"Programme for the International Assessment of Adult Competencies"` returns nothing because the deposited title omits *the*; `"PIAAC"` returns the survey.
- Keep the default relevance sort when the title is known. Sorting by date discards relevance and returns unrelated recent deposits.

Add an unquoted year alongside a quoted phrase to rank a specific cycle first, for example `"Survey of Household Spending" 2023`.

## Finding a survey and its cycles

- ``Search Borealis for `"Survey of Household Spending"` and list the cycles.``
- ``Which years of `"Canadian Income Survey"` are available?``
- ``Find all `"Democracy Checkup"` cycles.``
- ``Search for `"Canadian Election Study"`. Which election years are covered?``

Verified counts for common holdings, each returning the survey itself as the top result:

| Survey | Matches | Survey | Matches |
| --- | --- | --- | --- |
| `"Labour Force Survey"` | 2084 | `"Census of Population"` | 735 |
| `"Postal Code Conversion File"` | 242 | `"Census of Agriculture"` | 108 |
| `"General Social Survey"` | 135 | `"Canadian Community Health Survey"` | 106 |
| `"Survey of Household Spending"` | 183 | `"National Household Survey"` | 63 |
| `"Canadian Business Patterns"` | 51 | `"Employment Insurance Coverage Survey"` | 50 |
| `"Canadian Election Study"` | 39 | `"National Graduates Survey"` | 37 |
| `"National Travel Survey"` | 37 | `"Discharge Abstract Database"` | 29 |
| `"Canadian Income Survey"` | 22 | `"Survey of Financial Security"` | 14 |
| `"Canadian Housing Survey"` | 11 | `"Tuition and Living Accommodation Costs"` | 9 |
| `"Canadian Tobacco and Nicotine Survey"` | 8 | `"Democracy Checkup"` | 7 |
| `"Survey on Early Learning and Child Care Arrangements"` | 7 | `"Canadian Survey on Working Conditions"` | 2 |
| `"Indigenous Peoples Survey"` | 2 | `"Mental Health and Access to Care Survey"` | 2 |

## Files, formats, and access

- For ``"Labour Force Survey"`` February 2024, what formats is the microdata in, and is anything restricted?
- `List every file in the Canadian Community Health Survey 2022 Annual Component with size and format.`
- ``Does `"Survey of Financial Security"` 2019 include SPSS or SAS setup files?``

The February 2024 Labour Force Survey returns a 10.9 MB tab-delimited microdata file, a 2.4 MB archive, a codebook archive, and five PDF guides, none restricted.

## Survey documentation

Requires the `pdf` optional dependency.

- `Open the CCHS 2022 user guide and explain how the income variables are derived.`
- `What does the Labour Force Survey guide say about the 2025 rebasing?`
- `Read the data dictionary for CCHS 2022 and list the derived variables.`
- `Summarise the sampling design section of the Indigenous Peoples Survey documentation.`

`CCHS_2022_User_Guide.pdf` extracts to 3008 lines of text, retrievable in bounded line ranges.

## Microdata profiling

- ``Profile the Labour Force Survey February 2024 microdata and show the distribution of `LFSSTAT`.``
- `How many columns are in the National Travel Survey 2022 visit file, and which have missing values?`

Profiling the 10.9 MB Labour Force Survey file reads 100000 rows and returns per-column statistics, for example `LFSSTAT` with four distinct values distributed 53626, 37835, 4741, and 3798. Profiling files of this size requires `BOREALIS_MAX_FILE_BYTES` at its 25 MB default rather than a smaller limit.

Profile statistics describe rows read from a file. They do not establish that one row represents one person, household, or observation; the survey documentation establishes that.

## Multi-step research questions

- `Find the CCHS 2022 PUMF, profile the main data file, then use the user guide to explain what the most frequent variables mean.`
- ``Compare the file lists of `"Canadian Election Study"` 2021 and 2025. What changed?``
- ``I need postal code geography for the 2021 Census. Which `"Postal Code Conversion File"` version should I use, and what documentation comes with it?``

## Institution and geography

An institution filter limits results to a publishing Dataverse subtree. A geographic filter describes the place a dataset is about. The two answer different questions.

- ``Which `"Labour Force Survey"` datasets were published by University of Toronto?``
- `Find water quality datasets about Alberta.`
- `What is the difference between datasets from University of Alberta and datasets about Alberta?`

Geographic coverage metadata is sparsely populated in Borealis. Province and country filters return usable result sets, while city filters return very few matches even for major cities, so a city filter that returns nothing usually reflects missing metadata rather than an absent dataset.

## Questions this toolkit cannot answer

- **Codebooks distributed as archives.** Files such as `LFS_PUMF_EPA_FGMD_codebook.zip` are listed but not extracted, so value labels are unavailable unless a PDF guide in the same dataset documents them.
- **Scanned PDFs.** A PDF with no text layer is reported as such rather than returned empty.
- **Proprietary microdata formats.** SPSS, Stata, and Excel files are listed but not parsed.
- **Restricted content.** Files restricted in Borealis require a token with access to them.

See [`../README.md`](../README.md) for installation and for connecting the toolkit to Claude, ChatGPT, and other MCP hosts.
