from github_collector import config

def test_db_url_exists():
    assert hasattr(config, "DB_URL")
    assert config.DB_URL.startswith("sqlite:///")

def test_log_dir_exists():
    assert hasattr(config, "LOG_DIR")
    assert config.LOG_DIR.exists()
