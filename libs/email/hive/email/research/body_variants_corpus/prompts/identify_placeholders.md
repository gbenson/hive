# Task

You will be provided with the plain text (text/plain) version of an
email that also has an HTML (text/html) version.  Read the provided
plain text version carefully, then categorize it and respond with a
valid JSON object as detailed below.

# Categories

- Categorize the plain text version as **complete** if it appears
  to be a substantially complete alternative rendering of the HTML
  version.  Focus strictly on the content rather than formatting
  or presentation.

- Categorize the plain text version as **placeholder** if it seems
  that all or most of the HTML version's content has been replaced
  with a link to the HTML version.

# Response

Respond with a valid JSON object of the following format:

```
{"category": "(complete|placeholder)"}
```

Output only this JSON object, not the triple-quotes.

# Example

Input:

```
...blah blah blah blah blah...

For a full version of this email please go here:
https://view.email.example.com/?e=47e2c759b8d9a3ec706c0cf0d5300cf0

...blah blah blah blah blah...
```

Response:
```
{"category": "placeholder"}
```
