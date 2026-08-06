# Method card: YouTube Data API

## Identity and data model

A YouTube channel ID identifies a source account, not a human. The adapter emits channel subjects as `kind: account`; title and custom URL/handle are mutable aliases. A video is a distinct Work, related to and contributed by the publishing channel account. The operating person or organisation is unresolved unless another source supplies literal evidence.

Stable source-native identifiers:

- `youtube_channel_id` for a channel account;
- `youtube_video_id` for a video;
- `youtube_handle` as a mutable source-scoped alias, never a global person identifier.

## Persisted fields

The pilot keeps the minimal evidence-first set needed for source identity and temporal routing: IDs, title, publication time, selected status/type fields, source digest, endpoint, and the channel/video relationship. It deliberately excludes descriptions, tags, statistics, thumbnails, comments, transcripts, audio, and video.

## Policy boundary

Official policy references:

- <https://developers.google.com/youtube/terms/developer-policies>
- <https://developers.google.com/youtube/terms/api-services-terms-of-service>
- <https://developers.google.com/youtube/v3/getting-started>

The current reviewed policy requires stored API data to be refreshed or deleted within 30 days unless a documented current exception applies. The adapter records `refresh_required_days: 30`, keeps YouTube data source-separated, and does not produce a universal or cross-platform score.

## Scale verdict

`research_more`. Run only a bounded, quota-budgeted sample after rechecking the exact 2026 policy and retention behavior. It is valuable for stable channel/video IDs but weaker than publisher RSS for human role evidence.
