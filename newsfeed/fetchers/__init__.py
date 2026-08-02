from newsfeed.fetchers import hackernews, papers

FETCHERS = {
    "hackernews": hackernews.fetch,
    "papers": papers.fetch,
}
