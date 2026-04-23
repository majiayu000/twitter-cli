from __future__ import annotations

from twitter_cli.client import TwitterClient
from twitter_cli.parser import _deep_get, parse_explore_timeline_response, parse_timeline_response


def _make_client() -> TwitterClient:
    client = TwitterClient.__new__(TwitterClient)
    client._ct_init_attempted = True
    client._client_transaction = None
    client._request_delay = 0.0
    client._max_retries = 0
    client._retry_base_delay = 0.0
    client._max_count = 200
    return client


def test_parse_home_timeline_fixture(fixture_loader) -> None:
    payload = fixture_loader("home_timeline.json")

    tweets, cursor = parse_timeline_response(
        payload,
        lambda data: _deep_get(data, "data", "home", "home_timeline_urt", "instructions"),
    )

    assert [tweet.id for tweet in tweets] == ["1", "20"]
    assert cursor == "cursor-bottom-1"
    assert tweets[0].media[0].type == "photo"
    # note_tweet full text should be preferred over legacy.full_text for long tweets
    assert "Show More" in tweets[0].text
    assert tweets[0].text.startswith("Hello\nworld\n")
    assert tweets[0].urls == ["https://example.com/post"]
    assert tweets[1].is_retweet is True
    assert tweets[1].retweeted_by == "bob"
    assert tweets[1].quoted_tweet is not None
    assert tweets[1].quoted_tweet.id == "30"


def test_parse_home_timeline_fixture_marks_promoted_entries(fixture_loader) -> None:
    payload = fixture_loader("home_timeline.json")
    entry = payload["data"]["home"]["home_timeline_urt"]["instructions"][0]["entries"][0]
    entry["entryId"] = "promoted-tweet-1-demo"
    entry["content"]["itemContent"]["promotedMetadata"] = {"impressionId": "demo"}

    tweets, _ = parse_timeline_response(
        payload,
        lambda data: _deep_get(data, "data", "home", "home_timeline_urt", "instructions"),
    )

    assert tweets[0].is_promoted is True
    assert tweets[1].is_promoted is False


def test_parse_tweet_detail_fixture_with_nested_items(fixture_loader) -> None:
    payload = fixture_loader("tweet_detail.json")

    tweets, cursor = parse_timeline_response(
        payload,
        lambda data: _deep_get(data, "data", "threaded_conversation_with_injections_v2", "instructions"),
    )

    assert [tweet.id for tweet in tweets] == ["100", "101"]
    assert cursor == "conversation-cursor"


def test_parse_search_timeline_fixture_with_module_items(fixture_loader) -> None:
    payload = fixture_loader("search_timeline.json")

    tweets, cursor = parse_timeline_response(
        payload,
        lambda data: _deep_get(data, "data", "search_by_raw_query", "search_timeline", "timeline", "instructions"),
    )

    assert [tweet.id for tweet in tweets] == ["500"]
    assert cursor == "search-cursor"
    assert tweets[0].media[0].type == "video"
    assert tweets[0].media[0].url == "https://video-high.mp4"


def test_parse_explore_timeline_trends_from_module_items() -> None:
    payload = {
        "data": {
            "timeline": {
                "timeline": {
                    "instructions": [
                        {
                            "entries": [
                                {
                                    "content": {
                                        "entryType": "TimelineTimelineModule",
                                        "items": [
                                            {
                                                "entryId": "trend-1",
                                                "item": {
                                                    "itemContent": {
                                                        "__typename": "TimelineTrend",
                                                        "itemType": "TimelineTrend",
                                                        "name": "OpenAI launches feature",
                                                        "is_ai_trend": True,
                                                        "social_context": {
                                                            "text": "4 hours ago · News · 195 posts",
                                                            "contextImageUrls": ["https://example.com/a.jpg"],
                                                        },
                                                        "trend_url": {
                                                            "url": "twitter://trending/12345",
                                                            "urlType": "DeepLink",
                                                        },
                                                    }
                                                },
                                            }
                                        ],
                                    }
                                },
                                {
                                    "content": {
                                        "entryType": "TimelineTimelineCursor",
                                        "cursorType": "Bottom",
                                        "value": "cursor-next",
                                    }
                                },
                            ]
                        }
                    ]
                }
            }
        }
    }

    items, cursor = parse_explore_timeline_response(
        payload,
        lambda data: _deep_get(data, "data", "timeline", "timeline", "instructions"),
        section="news",
    )

    assert cursor == "cursor-next"
    assert len(items) == 1
    assert items[0].id == "12345"
    assert items[0].name == "OpenAI launches feature"
    assert items[0].section == "news"
    assert items[0].category == "News"
    assert items[0].time_context == "4 hours ago"
    assert items[0].post_count_text == "195 posts"
    assert items[0].is_ai_trend is True


def test_parse_list_timeline_fixture_with_visibility_wrapper(fixture_loader) -> None:
    payload = fixture_loader("list_timeline.json")

    tweets, cursor = parse_timeline_response(
        payload,
        lambda data: _deep_get(data, "data", "list", "tweets_timeline", "timeline", "instructions"),
    )

    assert [tweet.id for tweet in tweets] == ["700"]
    assert cursor == "list-cursor"
    assert tweets[0].author.verified is True
    assert tweets[0].lang == "zh"
    assert tweets[0].is_subscriber_only is True


def test_fetch_user_list_with_fixture(monkeypatch, fixture_loader) -> None:
    client = _make_client()
    payload = fixture_loader("followers_page.json")
    monkeypatch.setattr(client, "_graphql_get", lambda operation_name, variables, features: payload)

    users = client._fetch_user_list(
        "Followers",
        "user-id",
        20,
        lambda data: _deep_get(data, "data", "user", "result", "timeline", "timeline", "instructions"),
    )

    assert len(users) == 1
    assert users[0].screen_name == "follower1"
    assert users[0].verified is True
