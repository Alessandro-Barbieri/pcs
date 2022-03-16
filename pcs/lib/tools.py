import os
import tempfile
import uuid
from contextlib import contextmanager
from typing import (
    Any,
    Union,
)

from pcs.common import reports
from pcs.lib.errors import LibraryError


def generate_binary_key(random_bytes_count):
    return os.urandom(random_bytes_count)


def generate_uuid() -> str:
    return uuid.uuid4().hex


def environment_file_to_dict(config):
    """
    Parse systemd Environment file. This parser is simplified version of
    parser in systemd, because of their poor implementation.
    Returns configuration in dictionary in format:
    {
        <option>: <value>,
        ...
    }

    config -- Environment file as string
    """
    # escape new lines
    config = config.replace("\\\n", "")

    data = {}
    for line in [l.strip() for l in config.split("\n")]:
        if line == "" or line.startswith("#") or line.startswith(";"):
            continue
        if "=" not in line:
            continue
        key, val = line.split("=", 1)
        value = val.strip()
        data[key.strip()] = value
    return data


def dict_to_environment_file(config_dict):
    """
    Convert data in dictionary to Environment file format.
    Returns Environment file as string in format:
    # comment
    <option>=<value>
    ...

    config_dict -- dictionary in format: { <option>: <value>, ...}
    """
    lines = ["# This file has been generated by pcs.\n"]
    for key, val in sorted(config_dict.items()):
        lines.append("{key}={val}\n".format(key=key, val=val))
    return "".join(lines)


def write_tmpfile(data, binary=False):
    """
    Write data to a new tmp file and return the file; raises EnvironmentError.
    DEPRECATED: use get_tmp_file context manager

    string or bytes data -- data to write to the file
    bool binary -- treat data as binary?
    """
    # pylint: disable=consider-using-with
    mode = "w+b" if binary else "w+"
    tmpfile = tempfile.NamedTemporaryFile(mode=mode, suffix=".pcs")
    if data is not None:
        tmpfile.write(data)
        tmpfile.flush()
    return tmpfile


@contextmanager
def get_tmp_file(
    data: Union[None, bytes, str] = None,
    binary: bool = False,
) -> Any:
    mode = "w+b" if binary else "w+"
    tmpfile = None
    try:
        with tempfile.NamedTemporaryFile(mode=mode, suffix=".pcs") as tmpfile:
            if data is not None:
                tmpfile.write(data)
                tmpfile.flush()
            yield tmpfile
    finally:
        if tmpfile:
            tmpfile.close()


@contextmanager
def get_tmp_cib(report_processor: reports.ReportProcessor, data: str) -> Any:
    try:
        with get_tmp_file(data) as tmp_cib_file:
            report_processor.report(
                reports.ReportItem.debug(
                    reports.messages.TmpFileWrite(tmp_cib_file.name, data)
                )
            )
            yield tmp_cib_file
    except EnvironmentError as e:
        raise LibraryError(
            reports.ReportItem.error(reports.messages.CibSaveTmpError(str(e)))
        ) from e


def create_tmp_cib(report_processor: reports.ReportProcessor, data: str) -> Any:
    try:
        tmp_file = write_tmpfile(data)
        report_processor.report(
            reports.ReportItem.debug(
                reports.messages.TmpFileWrite(tmp_file.name, data)
            )
        )
        return tmp_file
    except EnvironmentError as e:
        raise LibraryError(
            reports.ReportItem.error(reports.messages.CibSaveTmpError(str(e)))
        ) from e
