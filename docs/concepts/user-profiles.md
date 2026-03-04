# User Profiles

`GET /api/v1/profile` returns compact context:

- `static`: stable facts/preferences
- `dynamic`: recent or changing context

Optional `q` adds relevant search results in the same response.

Use profile output in system prompts to personalize responses while keeping prompts compact.
