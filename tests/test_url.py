def test_extract_video_id_from_watch_url():
    """Test extracting video ID from standard YouTube watch URL"""
    from main import extract_video_id
    
    url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    
    video_id = extract_video_id(url)
    
    assert video_id == "dQw4w9WgXcQ"


def test_extract_video_id_from_short_url():
    """Test extracting video ID from youtu.be short URL"""
    from main import extract_video_id
    
    url = "https://youtu.be/dQw4w9WgXcQ"
    
    video_id = extract_video_id(url)
    
    assert video_id == "dQw4w9WgXcQ"


def test_extract_video_id_returns_id_if_already_extracted():
    """Test that plain video ID is returned as-is"""
    from main import extract_video_id
    
    video_id = extract_video_id("dQw4w9WgXcQ")
    
    assert video_id == "dQw4w9WgXcQ"
