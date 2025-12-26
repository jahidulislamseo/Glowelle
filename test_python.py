
def test_basic_execution():
    try:
        with open("test_log.txt", "w") as f:
            f.write("Python is running!")
        assert True
    except Exception as e:
        assert False, f"Error: {e}"
