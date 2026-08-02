from newsfeed.fetchers import hackernews, models_hub, papers

FETCHERS = {
    "hackernews": hackernews.fetch,
    "papers": papers.fetch,
    "models": models_hub.fetch,
}
