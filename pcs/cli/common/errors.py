from typing import (
    List,
    Optional,
)

from pcs.common.str_tools import (
    format_list_base,
    quote_items,
)

ERR_NODE_LIST_AND_ALL_MUTUALLY_EXCLUSIVE = (
    "Cannot specify both --all and a list of nodes."
)

SEE_MAN_CHANGES = "See 'man pcs' -> Changes in pcs-{}."


def _msg_command_replaced(new_commands: List[str], pcs_version: str) -> str:
    return "This command has been replaced with {commands}. {changes}".format(
        commands=format_list_base(quote_items(new_commands)),
        changes=SEE_MAN_CHANGES.format(pcs_version),
    )


def raise_command_replaced(new_commands: List[str], pcs_version: str) -> None:
    raise CmdLineInputError(
        message=_msg_command_replaced(new_commands, pcs_version=pcs_version)
    )


class CmdLineInputError(Exception):
    """
    Exception express that user entered incorrect commad in command line.
    """

    def __init__(
        self,
        message: Optional[str] = None,
        hint: Optional[str] = None,
        show_both_usage_and_message: bool = False,
    ) -> None:
        """
        message -- explains what was wrong with the entered command
        hint -- provides an additional hint how to proceed
        show_both_usage_and_message -- show both the message and usage

        The routine which handles this exception behaves according to whether
        the message was specified (prints this message to user) or not (prints
        appropriate part of documentation). If show_both_usage_and_message is
        True, documentation will be printed first and the message will be
        printed after that. Hint is printed every time as the last item.
        """
        super().__init__(message)
        self.message = message
        self.hint = hint
        self.show_both_usage_and_message = show_both_usage_and_message
