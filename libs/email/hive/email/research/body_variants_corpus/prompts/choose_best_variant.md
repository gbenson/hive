### Task

You are provided with a JSON document containing two versions of the
same `multipart/alternative` email: one is plain text from the
`text/plain` alternative, and the other is markdown generated from the
`text/html` alternative. Your task is to analyze both versions and
determine which one is best suited for further textual analysis,
focusing strictly on the content rather than formatting or
presentation.


### Criteria

1. **Preference for Plain Text**: Opt for the plain text version if it
     includes all the important information found in the markdown
     version and they are equal in content.


2. **Use of Markdown Version**: Choose the markdown version if:

     - The plain text version is missing crucial information present
       in the markdown version.

     - The markdown version contains important information not present
       in the plain text.


3. **Link Evaluation**: Treat clickable links and plain URLs as the
     same if they link to the same URL in identical contexts.


4. **Image and Formatting Ignorance**: Ignore differences in
     formatting and any image links unless they form core information
     necessary for understanding the message (e.g., descriptive image
     URLs).


5. **Boilerplate Exclusion**:

     - Exclude legal text, copyright messages, advertisements,
       addresses, unsubscription links, special offer links, and
       similar boilerplate.

     - Note that boilerplate and ignorable content are often located
       towards the end of the message or in the signature area.

     - Preserve any core legal content that is part of the substantive
       message, especially pertaining to legal discussions, contacts,
       terms, conditions, policies, or guidelines.


6. **Core Information Minimization**: When assessing meaningfulness,
     consider if information would be included when condensing the
     message to its minimal form without losing intended key content.


7. **Decisive Choice**: Choose the version that fully contains all
     essential information unambiguously, ignoring merely formatting
     aspects if they are not part of the core message.


8. **No Guessing**: If both versions contain important, unique
     information, respond with **"not-decidable"** and provide a concise
     explanation of the non-shared information in each version.


### Instructions

- Digest and understand the criteria focused solely on content.

- Thoroughly read both the plain text and markdown versions for their
  content.

- Fully process all information contained in both variants.

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
