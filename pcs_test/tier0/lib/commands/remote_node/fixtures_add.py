import base64

from pcs import settings
from pcs.common import file_type_codes
from pcs.common.reports import codes as report_codes

from pcs_test.tools import fixture

OFFLINE_ERROR_MSG = "Could not resolve host"
FAIL_HTTP_KWARGS = dict(
    output="",
    was_connected=False,
    errno="6",
    error_msg=OFFLINE_ERROR_MSG,
)


class EnvConfigMixin:
    def __init__(self, call_collection, wrap_helper, config):
        del wrap_helper, call_collection
        self.config = config

    def distribute_authkey(
        self, communication_list, pcmk_authkey_content, result=None, **kwargs
    ):
        if kwargs.get("was_connected", True):
            result = (
                result
                if result is not None
                else {
                    "code": "written",
                    "message": "",
                }
            )

            kwargs["results"] = {"pacemaker_remote authkey": result}
        elif result is not None:
            raise AssertionError(
                "Keyword 'result' makes no sense with 'was_connected=False'"
            )
        self.config.http.put_file(
            communication_list=communication_list,
            files={
                "pacemaker_remote authkey": {
                    "type": "pcmk_remote_authkey",
                    "data": base64.b64encode(pcmk_authkey_content).decode(
                        "utf-8"
                    ),
                    "rewrite_existing": True,
                }
            },
            **kwargs,
        )

    def get_host_info(self, label, dest_list, output=None):
        if output is None:
            output = dict(
                services=dict(
                    pacemaker_remote=dict(
                        installed=True, enabled=False, running=False
                    ),
                ),
                cluster_configuration_exists=False,
            )
        self.config.http.host.get_host_info(
            communication_list=[
                {
                    "label": label,
                    "dest_list": dest_list,
                },
            ],
            output_data=output,
        )

    def authkey_exists(self, return_value):
        self.config.raw_file.exists(
            file_type_codes.PACEMAKER_AUTHKEY,
            settings.pacemaker_authkey_file,
            exists=return_value,
        )

    def open_authkey(self, pcmk_authkey_content="", fail=False):
        self.config.raw_file.read(
            file_type_codes.PACEMAKER_AUTHKEY,
            settings.pacemaker_authkey_file,
            content=(pcmk_authkey_content if not fail else None),
            exception_msg=("open failed" if fail else None),
        )

    def push_existing_authkey_to_remote(
        self, host_name, dest_list, distribution_result=None
    ):
        pcmk_authkey_content = b"password"
        (
            self.config.local.authkey_exists(return_value=True)
            .local.open_authkey(pcmk_authkey_content)
            .local.distribute_authkey(
                communication_list=[dict(label=host_name, dest_list=dest_list)],
                pcmk_authkey_content=pcmk_authkey_content,
                result=distribution_result,
            )
        )

    def run_pacemaker_remote(self, label, dest_list, result=None, **kwargs):
        if kwargs.get("was_connected", True):
            result = (
                result
                if result is not None
                else {
                    "code": "success",
                    "message": "",
                }
            )

            kwargs["results"] = {
                "pacemaker_remote enable": result,
                "pacemaker_remote start": result,
            }
        elif result is not None:
            raise AssertionError(
                "Keyword 'result' makes no sense with 'was_connected=False'"
            )

        self.config.http.manage_services(
            communication_list=[dict(label=label, dest_list=dest_list)],
            action_map={
                "pacemaker_remote enable": {
                    "type": "service_command",
                    "service": "pacemaker_remote",
                    "command": "enable",
                },
                "pacemaker_remote start": {
                    "type": "service_command",
                    "service": "pacemaker_remote",
                    "command": "start",
                },
            },
            **kwargs,
        )


REPORTS = (
    fixture.ReportStore()
    .info(
        "authkey_distribution_started",
        report_codes.FILES_DISTRIBUTION_STARTED,
        file_list=["pacemaker authkey"],
    )
    .info(
        "authkey_distribution_success",
        report_codes.FILE_DISTRIBUTION_SUCCESS,
        file_description="pacemaker authkey",
    )
    .info(
        "pcmk_remote_start_enable_started",
        report_codes.SERVICE_COMMANDS_ON_NODES_STARTED,
        action_list=[
            "pacemaker_remote start",
            "pacemaker_remote enable",
        ],
    )
    .info(
        "pcmk_remote_enable_success",
        report_codes.SERVICE_COMMAND_ON_NODE_SUCCESS,
        service_command_description="pacemaker_remote enable",
    )
    .info(
        "pcmk_remote_start_success",
        report_codes.SERVICE_COMMAND_ON_NODE_SUCCESS,
        service_command_description="pacemaker_remote start",
    )
)

EXTRA_REPORTS = (
    fixture.ReportStore()
    .error(
        "manage_services_connection_failed",
        report_codes.NODE_COMMUNICATION_ERROR_UNABLE_TO_CONNECT,
        command="remote/manage_services",
        reason=OFFLINE_ERROR_MSG,
        force_code=report_codes.SKIP_OFFLINE_NODES,
    )
    .as_warn(
        "manage_services_connection_failed",
        "manage_services_connection_failed_warn",
    )
    .copy(
        "manage_services_connection_failed",
        "put_file_connection_failed",
        command="remote/put_file",
    )
    .as_warn(
        "put_file_connection_failed",
        "put_file_connection_failed_warn",
    )
    .error(
        "pcmk_remote_enable_failed",
        report_codes.SERVICE_COMMAND_ON_NODE_ERROR,
        reason="Operation failed.",
        service_command_description="pacemaker_remote enable",
        force_code=report_codes.FORCE,
    )
    .as_warn("pcmk_remote_enable_failed", "pcmk_remote_enable_failed_warn")
    .copy(
        "pcmk_remote_enable_failed",
        "pcmk_remote_start_failed",
        service_command_description="pacemaker_remote start",
    )
    .as_warn("pcmk_remote_start_failed", "pcmk_remote_start_failed_warn")
    .error(
        "authkey_distribution_failed",
        report_codes.FILE_DISTRIBUTION_ERROR,
        reason="File already exists",
        file_description="pacemaker authkey",
        force_code=report_codes.FORCE,
    )
    .as_warn("authkey_distribution_failed", "authkey_distribution_failed_warn")
)


def fixture_reports_not_live_cib(node_name):
    return [
        fixture.info(
            report_codes.COROSYNC_NODE_CONFLICT_CHECK_SKIPPED,
            reason_type="not_live_cib",
        ),
        fixture.info(
            report_codes.FILES_DISTRIBUTION_SKIPPED,
            reason_type="not_live_cib",
            file_list=["pacemaker authkey"],
            node_list=[node_name],
        ),
        fixture.info(
            report_codes.SERVICE_COMMANDS_ON_NODES_SKIPPED,
            reason_type="not_live_cib",
            action_list=[
                "pacemaker_remote start",
                "pacemaker_remote enable",
            ],
            node_list=[node_name],
        ),
    ]


def fixture_reports_new_node_unreachable(node_name, omitting=False):
    if omitting:
        report = [
            fixture.warn(
                report_codes.OMITTING_NODE,
                node=node_name,
            ),
        ]
    else:
        report = [
            fixture.warn(
                report_codes.HOST_NOT_FOUND,
                host_list=[node_name],
            ),
        ]
    return report + [
        fixture.info(
            report_codes.FILES_DISTRIBUTION_SKIPPED,
            reason_type="unreachable",
            file_list=["pacemaker authkey"],
            node_list=[node_name],
        ),
        fixture.info(
            report_codes.SERVICE_COMMANDS_ON_NODES_SKIPPED,
            reason_type="unreachable",
            action_list=["pacemaker_remote start", "pacemaker_remote enable"],
            node_list=[node_name],
        ),
    ]
