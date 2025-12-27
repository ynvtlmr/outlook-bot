import subprocess

from outlook_client import OutlookClient, get_outlook_version


def test_run_script_success(mocker):
    mocker.patch("os.path.exists", return_value=True)
    mocker.patch("subprocess.run", return_value=mocker.Mock(stdout="Output", returncode=0))

    client = OutlookClient("/scripts")
    res = client._run_script("test.scpt")
    assert res == "Output"


def test_run_script_failure(mocker):
    mocker.patch("os.path.exists", return_value=True)
    mocker.patch("subprocess.run", side_effect=subprocess.CalledProcessError(1, "cmd"))

    client = OutlookClient("/scripts")
    # Exception is caught and logged, returning None
    res = client._run_script("test.scpt")
    assert res is None


def test_get_outlook_version(mocker):
    # Mock osascript output
    mocker.patch("subprocess.run", return_value=mocker.Mock(stdout="16.0", returncode=0))
    ver = get_outlook_version()
    assert ver == "16.0"


def test_reply_to_message(mocker):
    mocker.patch("os.path.exists", return_value=True)
    mock_run = mocker.patch("subprocess.run", return_value=mocker.Mock(stdout="Done", returncode=0))

    client = OutlookClient("/scripts")
    client.reply_to_message("msg1", "Body")

    # Check arguments
    args = mock_run.call_args[0][0]
    assert "msg1" in args
    assert "Body" in args


def test_activate_outlook(mocker):
    """Test calling activate_outlook script."""
    mocker.patch("os.path.exists", return_value=True)
    mock_run = mocker.patch("subprocess.run", return_value=mocker.Mock(stdout="", returncode=0))

    client = OutlookClient("/scripts")
    client.activate_outlook()

    # Verify correct script name was used
    args = mock_run.call_args[0][0]
    assert "activate_outlook.scpt" in args[-1]
