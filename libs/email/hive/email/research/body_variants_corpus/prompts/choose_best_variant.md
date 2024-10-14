### Task

You are provided with a JSON document containing two versions of the
same `multipart/alternative` email: one is plain text from the
`text/plain` alternative, and the other is markdown generated from the
`text/html` alternative. Your task is to analyze both versions and
determine which one is best suited for further textual analysis based
on specific criteria below, focusing strictly on the content rather
than formatting or presentation.

### Criteria

1. **Preference for Plain Text**: Opt for the plain text version if it
     includes all the important information found in the markdown
     version, as long as they are equal in content.

2. **Use of Markdown Version**: Choose the markdown version if:
     - The plain text version is missing crucial information present
       in the markdown version.
     - The markdown version contains information needed that the plain
       text lacks.

3. **Boilerplate Exclusion**: Exclude legal text, copyright messages,
     advertisements, unsubscription links, and similar boilerplate
     content. Be careful not to mistake substantive legal messages for
     boilerplate content.

4. **Decisive Choice**: If one version contains all important
     information present in the other version, opt for that version
     unambiguously. Ignore differences in formatting or visual
     presentation aspects.

5. **No Guessing**: If both versions contain important, unique
     information, respond with **"not-decidable"** and provide a concise
     1-4 sentence explanation of the non-shared information in each
     version in your response.

### Instructions

- Digest and understand the criteria strictly focused on content.
- Thoroughly read both the plain text and markdown versions for content.
- Fully digest and understand all information contained in both variants.
- Evaluate the BEST_VERSION based on the criteria above. Choose one of
  these literal string values:
  - **"plain"** if the plain text variant is sufficient and complete.
  - **"markdown"** if the markdown variant is necessary for completeness.
  - **"not-decidable"** if both variants contain important but distinct
       information.

- Respond with a valid JSON object in the following structure:

```json
{
  "best_version": "(plain|markdown|not-decidable)",
  "explanation": "(explanation if best_version is not-decidable)"
}
```

- Only output this JSON object, without formatted code indicators.
