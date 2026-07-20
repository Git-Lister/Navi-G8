import pytest
from navi_agent.tools.file_tools import read_file, write_file, list_directory

@pytest.mark.asyncio
async def test_read_file(tmp_path):
    f = tmp_path / "test.txt"
    f.write_text("hello")
    result = await read_file(str(f))
    assert "hello" in result[0].text

@pytest.mark.asyncio
async def test_write_file(tmp_path):
    f = tmp_path / "new.txt"
    await write_file(str(f), "content")
    assert f.read_text() == "content"

@pytest.mark.asyncio
async def test_list_directory(tmp_path):
    (tmp_path / "a.txt").touch()
    (tmp_path / "b").mkdir()
    result = await list_directory(str(tmp_path))
    assert "a.txt" in result[0].text
    assert "b" in result[0].text