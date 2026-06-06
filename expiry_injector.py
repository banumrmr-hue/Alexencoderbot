EXPIRY_TEMPLATE = '''
import sys as _sys
import os as _os
import signal as _signal
import threading as _threading
import hashlib as _hashlib
import tempfile as _tempfile
from datetime import datetime as _datetime

_EXPIRY_DATE = "{expiry_date}"

_original_datetime_now = _datetime.now
_original_os_kill = _os.kill
_original_signal_signal = _signal.signal
_original_exit = _sys.exit
_original_os_exit = _os._exit


def _check_debugger():
    if _sys.gettrace() is not None or _sys.getprofile() is not None:
        print("Contact : @AlexEncoder")
        return True
    return False


def _get_self_code_hash():
    try:
        with open(__file__, 'rb') as _f:
            return _hashlib.sha256(_f.read()).hexdigest()
    except Exception:
        return None


_SELF_HASH = _get_self_code_hash()


def _check_code_integrity():
    if _SELF_HASH is not None:
        current_hash = _get_self_code_hash()
        if current_hash != _SELF_HASH:
            print("Contact : @AlexEncoder")
            return False
    return True


def _get_secure_time():
    try:
        import urllib.request as _ur
        import json as _json
        with _ur.urlopen('http://worldtimeapi.org/api/timezone/Etc/UTC', timeout=2) as _f:
            _data = _f.read().decode()
            _dt_str = _json.loads(_data)['datetime']
            return _datetime.strptime(_dt_str[:19], '%Y-%m-%dT%H:%M:%S').date()
    except Exception:
        return _original_datetime_now().date()


def _check_time_tamper(expiry_date_str):
    expiry_date = _datetime.strptime(expiry_date_str, '%Y-%m-%d').date()
    current_date = _get_secure_time()
    token_file = _os.path.join(_tempfile.gettempdir(), '.alex_expiry_token')
    try:
        with open(token_file, 'r') as _f:
            last_date_str = _f.read().strip()
            last_date = _datetime.strptime(last_date_str, '%Y-%m-%d').date()
            if last_date > current_date:
                print('Contact : @AlexEncoder')
                return True
    except Exception:
        pass
    with open(token_file, 'w') as _f:
        _f.write(current_date.strftime('%Y-%m-%d'))
    return current_date > expiry_date


_terminate_flag = False


def _monitor_loop(expiry_date_str):
    global _terminate_flag
    while not _terminate_flag:
        try:
            if _check_debugger() or not _check_code_integrity() or _check_time_tamper(expiry_date_str):
                print("Contact : @AlexEncoder")
                _original_os_kill(_os.getpid(), _signal.SIGKILL)
                _original_os_exit(1)
        except Exception:
            pass
        _threading.Event().wait(0.5)


def _check_expiry(expiry_date_str=_EXPIRY_DATE):
    try:
        for _sig in range(1, _signal.NSIG):
            if _sig not in (_signal.SIGKILL, _signal.SIGSTOP):
                try:
                    _original_signal_signal(_sig, _signal.SIG_DFL)
                except Exception:
                    pass
        _t = _threading.Thread(target=_monitor_loop, args=(expiry_date_str,), daemon=True)
        _t.start()
        if _check_debugger():
            raise Exception("Contact : @AlexEncoder")
        if not _check_code_integrity():
            raise Exception("Contact : @AlexEncoder")
        if _check_time_tamper(expiry_date_str):
            print('Contact : @AlexEncoder')
            input('')
            _pid = _os.getpid()
            try:
                _original_os_kill(_pid, _signal.SIGKILL)
            except Exception:
                pass
            _original_os_exit(1)
    except Exception as _e:
        print(f"Error: {{_e}}")
        _original_os_kill(_os.getpid(), _signal.SIGKILL)
        _original_os_exit(1)


_check_expiry()
'''


def run_expiry_injector(source_code: str, expiry_date: str) -> str:
    header = EXPIRY_TEMPLATE.format(expiry_date=expiry_date)
    return header + "\n" + source_code
