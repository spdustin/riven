import pytest

from RTN import Torrent, ParsedData
from testcontainers.postgres import PostgresContainer

from program.db.db import db, run_migrations
from program.media.item import MediaItem, Show, Season, Episode, Movie
from program.media.stream import Stream, StreamRelation, StreamBlacklistRelation
from program.db.db_functions import reset_streams, blacklist_stream, delete_media_item, delete_media_item_by_id, \
    delete_media_item_by_item_id, delete_media_items_by_ids, get_media_items_by_ids


@pytest.fixture(scope="session")
def test_container():
    with PostgresContainer("postgres:16.4-alpine3.20", username="postgres", password="postgres", dbname="riven", port=5432).with_bind_ports(5432, 5432) as postgres:
        yield postgres
@pytest.fixture(scope="function")
def test_scoped_db_session(test_container):
    run_migrations()
    session = db.Session()
    yield session
    session.close()
    db.drop_all()

def test_reset_streams_for_mediaitem_with_no_streams(test_scoped_db_session):
    media_item = MediaItem({"name":"MediaItem with No Streams"})
    media_item.item_id = "tt123456"
    test_scoped_db_session.add(media_item)
    test_scoped_db_session.commit()

    reset_streams(media_item)

    assert test_scoped_db_session.query(StreamRelation).filter_by(parent_id=media_item._id).count() == 0
    assert test_scoped_db_session.query(StreamBlacklistRelation).filter_by(media_item_id=media_item._id).count() == 0


def test_add_new_mediaitem_with_multiple_streams_and_reset_streams(test_scoped_db_session):
    media_item = MediaItem({"name":"New MediaItem"})
    media_item.item_id = "tt123456"
    stream1 = Stream(Torrent(
        raw_title="Example.Movie.2020.1080p.BluRay.x264-Example",
        infohash="997592a005d9c162391803c615975676738d6a11",
        data=ParsedData(parsed_title='Example Movie'),
        fetch=True,
        rank=150,
        lev_ratio=0.9
    ))
    stream2 = Stream(Torrent(
        raw_title="Example.Movie.2020.1080p.BluRay.x264-Example",
        infohash="c24046b60d764b2b58dce6fbb676bcd3cfcd257e",
        data=ParsedData(parsed_title='Example Movie'),
        fetch=True,
        rank=150,
        lev_ratio=0.8
    ))
    test_scoped_db_session.add(media_item)
    test_scoped_db_session.add(stream1)
    test_scoped_db_session.add(stream2)
    test_scoped_db_session.commit()

    stream_relation1 = StreamRelation(parent_id=media_item._id, child_id=stream1._id)
    stream_relation2 = StreamRelation(parent_id=media_item._id, child_id=stream2._id)
    test_scoped_db_session.add(stream_relation1)
    test_scoped_db_session.add(stream_relation2)
    test_scoped_db_session.commit()

    reset_streams(media_item)

    assert test_scoped_db_session.query(StreamRelation).filter_by(parent_id=media_item._id).count() == 0
    assert test_scoped_db_session.query(StreamBlacklistRelation).filter_by(media_item_id=media_item._id).count() == 0

def test_blacklists_active_stream(test_scoped_db_session):
    media_item = MediaItem({"name":"New MediaItem"})
    media_item.item_id = "tt123456"
    stream = Stream(Torrent(
        raw_title="Example.Movie.2020.1080p.BluRay.x264-Example",
        infohash="997592a005d9c162391803c615975676738d6a11",
        data=ParsedData(parsed_title='Example Movie'),
        fetch=True,
        rank=150,
        lev_ratio=0.9
    ))
    test_scoped_db_session.add(media_item)
    test_scoped_db_session.add(stream)
    test_scoped_db_session.commit()
    stream_relation = StreamRelation(parent_id=media_item._id, child_id=stream._id)
    test_scoped_db_session.add(stream_relation)
    test_scoped_db_session.commit()

    blacklist_stream(media_item, stream)

    assert test_scoped_db_session.query(StreamBlacklistRelation).filter_by(media_item_id=media_item._id, stream_id=stream._id).count() == 1

def test_successfully_resets_streams(test_scoped_db_session):
    media_item = MediaItem({"name":"New MediaItem"})
    media_item.item_id = "tt123456"
     
    stream1 = Stream(Torrent(
        raw_title="Example.Movie.2020.1080p.BluRay.x264-Example",
        infohash="997592a005d9c162391803c615975676738d6a11",
        data=ParsedData(parsed_title='Example Movie'),
        fetch=True,
        rank=150,
        lev_ratio=0.9
    ))

    stream2 = Stream(Torrent(
        raw_title="Example.Movie.2020.1080p.BluRay.x264-Example",
        infohash="c24046b60d764b2b58dce6fbb676bcd3cfcd257e",
        data=ParsedData(parsed_title='Example Movie'),
        fetch=True,
        rank=150,
        lev_ratio=0.8
    ))
    
    test_scoped_db_session.add(media_item)
    test_scoped_db_session.add(stream1)
    test_scoped_db_session.add(stream2)
    test_scoped_db_session.commit()

    stream_relation1 = StreamRelation(parent_id=media_item._id, child_id=stream1._id)
    stream_relation2 = StreamRelation(parent_id=media_item._id, child_id=stream2._id)
    test_scoped_db_session.add(stream_relation1)
    test_scoped_db_session.add(stream_relation2)
    test_scoped_db_session.commit()

    reset_streams(media_item)

    assert test_scoped_db_session.query(StreamRelation).filter_by(parent_id=media_item._id).count() == 0
    assert test_scoped_db_session.query(StreamBlacklistRelation).filter_by(media_item_id=media_item._id).count() == 0

def test_delete_media_item_success(test_scoped_db_session):
    media_item = MediaItem({"name":"New MediaItem"})
    media_item.item_id = "tt123456"
    test_scoped_db_session.add(media_item)

    stream1 = Stream(Torrent(
        raw_title="Example.Movie.2020.1080p.BluRay.x264-Example",
        infohash="997592a005d9c162391803c615975676738d6a11",
        data=ParsedData(parsed_title='Example Movie'),
        fetch=True,
        rank=150,
        lev_ratio=0.9
    ))
    test_scoped_db_session.add(stream1)
    test_scoped_db_session.commit()
    
    stream_relation1 = StreamRelation(parent_id=media_item._id, child_id=stream1._id)
    test_scoped_db_session.add(stream_relation1)
    test_scoped_db_session.commit()

    assert test_scoped_db_session.query(MediaItem).filter_by(_id=media_item._id).count() == 1
    assert test_scoped_db_session.query(StreamRelation).filter_by(parent_id=media_item._id).count() == 1
    assert test_scoped_db_session.query(Stream).filter_by(_id=stream1._id).count() == 1
    
    delete_media_item(media_item)

    assert test_scoped_db_session.query(MediaItem).filter_by(_id=media_item._id).count() == 0
    assert test_scoped_db_session.query(StreamRelation).filter_by(parent_id=media_item._id).count() == 0
    assert test_scoped_db_session.query(Stream).filter_by(_id=stream1._id).count() == 0

def test_delete_show_with_seasons_and_episodes_success(test_scoped_db_session):
    show = Show({"title": "New Show"})
    show.item_id = "tt654321"
    test_scoped_db_session.add(show)
    test_scoped_db_session.commit()

    season1 = Season({"number": 1, "parent": show})
    season1.parent_id = show._id
    test_scoped_db_session.add(season1)
    test_scoped_db_session.commit()

    episode1 = Episode({"number": 1})
    episode2 = Episode({"number": 2})
    episode1.parent_id = season1._id
    episode2.parent_id = season1._id
    test_scoped_db_session.add(episode1)
    test_scoped_db_session.add(episode2)
    test_scoped_db_session.commit()

    stream1 = Stream(Torrent(
        raw_title="Example.Show.S01E01.1080p.BluRay.x264-Example",
        infohash="abcd1234abcd1234abcd1234abcd1234abcd1234",
        data=ParsedData(parsed_title='Example Show'),
        fetch=True,
        rank=200,
        lev_ratio=0.95
    ))
    test_scoped_db_session.add(stream1)
    test_scoped_db_session.commit()

    stream_relation1 = StreamRelation(parent_id=show._id, child_id=stream1._id)
    test_scoped_db_session.add(stream_relation1)
    test_scoped_db_session.commit()

    assert test_scoped_db_session.query(Show).filter_by(_id=show._id).count() == 1
    assert test_scoped_db_session.query(Season).filter_by(parent_id=show._id).count() == 1
    assert test_scoped_db_session.query(Episode).filter_by(parent_id=season1._id).count() == 2
    assert test_scoped_db_session.query(StreamRelation).filter_by(parent_id=show._id).count() == 1
    assert test_scoped_db_session.query(Stream).filter_by(_id=stream1._id).count() == 1

    delete_media_item(show)

    assert test_scoped_db_session.query(Show).filter_by(_id=show._id).count() == 0
    assert test_scoped_db_session.query(Season).filter_by(parent_id=show._id).count() == 0
    assert test_scoped_db_session.query(Episode).filter_by(parent_id=season1._id).count() == 0
    assert test_scoped_db_session.query(StreamRelation).filter_by(parent_id=show._id).count() == 0
    assert test_scoped_db_session.query(Stream).filter_by(_id=stream1._id).count() == 0

def test_delete_show_by_id_with_seasons_and_episodes_success(test_scoped_db_session):
    show = Show({"title": "New Show"})
    show.item_id = "tt654321"
    test_scoped_db_session.add(show)
    test_scoped_db_session.commit()

    season1 = Season({"number": 1, "parent": show})
    season1.parent_id = show._id
    test_scoped_db_session.add(season1)
    test_scoped_db_session.commit()

    episode1 = Episode({"number": 1})
    episode2 = Episode({"number": 2})
    episode1.parent_id = season1._id
    episode2.parent_id = season1._id
    test_scoped_db_session.add(episode1)
    test_scoped_db_session.add(episode2)
    test_scoped_db_session.commit()

    stream1 = Stream(Torrent(
        raw_title="Example.Show.S01E01.1080p.BluRay.x264-Example",
        infohash="abcd1234abcd1234abcd1234abcd1234abcd1234",
        data=ParsedData(parsed_title='Example Show'),
        fetch=True,
        rank=200,
        lev_ratio=0.95
    ))
    test_scoped_db_session.add(stream1)
    test_scoped_db_session.commit()

    stream_relation1 = StreamRelation(parent_id=show._id, child_id=stream1._id)
    test_scoped_db_session.add(stream_relation1)
    test_scoped_db_session.commit()

    assert test_scoped_db_session.query(Show).filter_by(_id=show._id).count() == 1
    assert test_scoped_db_session.query(Season).filter_by(parent_id=show._id).count() == 1
    assert test_scoped_db_session.query(Episode).filter_by(parent_id=season1._id).count() == 2
    assert test_scoped_db_session.query(StreamRelation).filter_by(parent_id=show._id).count() == 1
    assert test_scoped_db_session.query(Stream).filter_by(_id=stream1._id).count() == 1

    delete_media_item_by_id(show._id)

    assert test_scoped_db_session.query(Show).filter_by(_id=show._id).count() == 0
    assert test_scoped_db_session.query(Season).filter_by(parent_id=show._id).count() == 0
    assert test_scoped_db_session.query(Episode).filter_by(parent_id=season1._id).count() == 0
    assert test_scoped_db_session.query(StreamRelation).filter_by(parent_id=show._id).count() == 0
    assert test_scoped_db_session.query(Stream).filter_by(_id=stream1._id).count() == 0

def test_delete_show_by_item_id_with_seasons_and_episodes_success(test_scoped_db_session):
    show = Show({"title": "New Show"})
    show.item_id = "tt654321"
    test_scoped_db_session.add(show)
    test_scoped_db_session.commit()

    season1 = Season({"number": 1, "parent": show})
    season1.parent_id = show._id
    test_scoped_db_session.add(season1)
    test_scoped_db_session.commit()

    episode1 = Episode({"number": 1})
    episode2 = Episode({"number": 2})
    episode1.parent_id = season1._id
    episode2.parent_id = season1._id
    test_scoped_db_session.add(episode1)
    test_scoped_db_session.add(episode2)
    test_scoped_db_session.commit()

    stream1 = Stream(Torrent(
        raw_title="Example.Show.S01E01.1080p.BluRay.x264-Example",
        infohash="abcd1234abcd1234abcd1234abcd1234abcd1234",
        data=ParsedData(parsed_title='Example Show'),
        fetch=True,
        rank=200,
        lev_ratio=0.95
    ))
    test_scoped_db_session.add(stream1)
    test_scoped_db_session.commit()

    stream_relation1 = StreamRelation(parent_id=show._id, child_id=stream1._id)
    test_scoped_db_session.add(stream_relation1)
    test_scoped_db_session.commit()

    assert test_scoped_db_session.query(Show).filter_by(_id=show._id).count() == 1
    assert test_scoped_db_session.query(Season).filter_by(parent_id=show._id).count() == 1
    assert test_scoped_db_session.query(Episode).filter_by(parent_id=season1._id).count() == 2
    assert test_scoped_db_session.query(StreamRelation).filter_by(parent_id=show._id).count() == 1
    assert test_scoped_db_session.query(Stream).filter_by(_id=stream1._id).count() == 1

    delete_media_item_by_item_id(show.item_id)

    assert test_scoped_db_session.query(Show).filter_by(_id=show._id).count() == 0
    assert test_scoped_db_session.query(Season).filter_by(parent_id=show._id).count() == 0
    assert test_scoped_db_session.query(Episode).filter_by(parent_id=season1._id).count() == 0
    assert test_scoped_db_session.query(StreamRelation).filter_by(parent_id=show._id).count() == 0
    assert test_scoped_db_session.query(Stream).filter_by(_id=stream1._id).count() == 0

def test_delete_media_items_by_ids_success(test_scoped_db_session):
    media_item1 = MediaItem({"name": "New MediaItem 1"})
    media_item1.item_id = "tt123456"
    test_scoped_db_session.add(media_item1)

    media_item2 = MediaItem({"name": "New MediaItem 2"})
    media_item2.item_id = "tt654321"
    test_scoped_db_session.add(media_item2)

    stream1 = Stream(Torrent(
        raw_title="Example.Movie.2020.1080p.BluRay.x264-Example",
        infohash="997592a005d9c162391803c615975676738d6a11",
        data=ParsedData(parsed_title='Example Movie'),
        fetch=True,
        rank=150,
        lev_ratio=0.9
    ))
    test_scoped_db_session.add(stream1)

    stream2 = Stream(Torrent(
        raw_title="Another.Movie.2021.720p.WEBRip.x264-Another",
        infohash="997592a005d9c162391803c615975676738d6a12",
        data=ParsedData(parsed_title='Another Movie'),
        fetch=True,
        rank=200,
        lev_ratio=0.85
    ))
    test_scoped_db_session.add(stream2)
    test_scoped_db_session.commit()

    stream_relation1 = StreamRelation(parent_id=media_item1._id, child_id=stream1._id)
    stream_relation2 = StreamRelation(parent_id=media_item2._id, child_id=stream2._id)
    test_scoped_db_session.add(stream_relation1)
    test_scoped_db_session.add(stream_relation2)
    test_scoped_db_session.commit()

    assert test_scoped_db_session.query(MediaItem).filter_by(_id=media_item1._id).count() == 1
    assert test_scoped_db_session.query(MediaItem).filter_by(_id=media_item2._id).count() == 1
    assert test_scoped_db_session.query(StreamRelation).filter_by(parent_id=media_item1._id).count() == 1
    assert test_scoped_db_session.query(StreamRelation).filter_by(parent_id=media_item2._id).count() == 1
    assert test_scoped_db_session.query(Stream).filter_by(_id=stream1._id).count() == 1
    assert test_scoped_db_session.query(Stream).filter_by(_id=stream2._id).count() == 1
    assert media_item1._id != media_item2._id

    delete_media_items_by_ids([media_item1._id, media_item2._id])

    assert test_scoped_db_session.query(MediaItem).filter_by(_id=media_item1._id).count() == 0
    assert test_scoped_db_session.query(MediaItem).filter_by(_id=media_item2._id).count() == 0
    assert test_scoped_db_session.query(StreamRelation).filter_by(parent_id=media_item1._id).count() == 0
    assert test_scoped_db_session.query(StreamRelation).filter_by(parent_id=media_item2._id).count() == 0
    assert test_scoped_db_session.query(Stream).filter_by(_id=stream1._id).count() == 0
    assert test_scoped_db_session.query(Stream).filter_by(_id=stream2._id).count() == 0

def test_get_media_items_by_ids_success(test_scoped_db_session):
    show = Show({"title": "Test Show"})
    show.item_id = "tt00112233"
    test_scoped_db_session.add(show)
    test_scoped_db_session.commit()

    season = Season({"number": 1, "parent": show})
    season.parent_id = show._id
    test_scoped_db_session.add(season)
    test_scoped_db_session.commit()

    episode1 = Episode({"number": 1})
    episode2 = Episode({"number": 2})
    episode1.parent_id = season._id
    episode2.parent_id = season._id
    test_scoped_db_session.add(episode1)
    test_scoped_db_session.add(episode2)
    test_scoped_db_session.commit()

    movie = Movie({"title": "Test Movie"})
    movie.item_id = "tt00443322"
    test_scoped_db_session.add(movie)
    test_scoped_db_session.commit()

    media_items = get_media_items_by_ids([show._id, season._id, episode1._id, episode2._id, movie._id])

    assert len(media_items) == 5

    assert any(isinstance(item, Show) and item._id == show._id for item in media_items)
    assert any(isinstance(item, Season) and item._id == season._id for item in media_items)
    assert any(isinstance(item, Episode) and item._id == episode1._id for item in media_items)
    assert any(isinstance(item, Episode) and item._id == episode2._id for item in media_items)
    assert any(isinstance(item, Movie) and item._id == movie._id for item in media_items)