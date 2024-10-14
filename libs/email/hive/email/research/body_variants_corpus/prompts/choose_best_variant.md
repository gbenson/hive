### Task

You are provided with a JSON document containing two versions of the
same `multipart/alternative` email: one is plain text taken from the
`text/plain` alternative, and one is markdown generated from the
`text/html` alternative. Your task is to analyze both versions and
determine which one is best suited for further textual analysis based
on the specific criteria below.

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
     information, respond with **"not-decidable"** and include
     a 1-4 sentence explanation of the non-shared information in
     each version in your response.

### Instructions

Take a step back and think step-by-step about how to achieve the best
outcome by following the instructions below:

- Fully digest and understand the criteria above.
- Thoroughly read both the plain text and markdown versions.
- Fully digest and understand all information contained both variants.
- Evaluate the BEST_VERSION based on the criteria above. This should
  be one of the following literal string values:
  - **"plain"** if the plain text variant is sufficient.
  - **"markdown"** if the markdown variant is necessary.
  - **"not-decidable"** if both variants contain important but
    distinct information.
- Respond with a valid JSON object with the following structure:

```json
{
  "best_version": "(plain|markdown|not-decidable)",
  "explanation": "(explanation if best_version is not-decidable)"
}
```

- You ONLY output this JSON object.
- You do not output the ``` code indicators, only the JSON object itself.
