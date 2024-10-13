### Task

You are provided with a JSON document containing two versions of the
same email: one in plain text and one in markdown format generated from
HTML. Your task is to analyze both versions and determine which one is
best suited for further textual analysis based on specific criteria.

### Criteria

1. **Preference for Plain Text**: Opt for the plain text version if it
     includes all the useful information from the email.

2. **Use of Markdown Version**: Choose the markdown version if:
     - The plain text version is overly summarized or replaced with
       a link to view an HTML version.
     - The markdown version contains important information that is
       missing from the plain text version.

3. **Boilerplate Exclusion**: Exclude legal text, copyright messages,
     advertisements, unsubscription links, and similar boilerplate
     content. However, be cautious not to mistake messages related to
     legal issues for boilerplate content.

4. **No Guessing**: If both versions contain important, unique
     information, respond with "no version contains all relevant
     information," followed by a breakdown of the information not
    shared by both versions.

### Instructions

- Thoroughly read both the plain text and markdown versions.
- Evaluate the information in both variants based on the criteria above.
- Respond with:
  - **"plain"** if the plain text variant is sufficient.
  - **"markdown"** if the markdown variant is necessary.
  - **"no version contains all relevant information"** if both variants
    contain important but distinct information.
