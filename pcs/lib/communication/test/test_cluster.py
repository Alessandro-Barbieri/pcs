from unittest import TestCase, skip

@skip("missing tests for pcs.lib.communication.cluster.Destroy")
class Destroy(TestCase):
    """
    tested in:
        pcs.lib.commands.test.cluster.test_setup.SetupSuccessMinimal
        pcs.lib.commands.test.cluster.test_setup.SetupSuccessAddresses
        pcs.lib.commands.test.cluster.test_setup.Setup2NodeSuccessMinimal
        pcs.lib.commands.test.cluster.test_setup.SetupWithWait
        pcs.lib.commands.test.cluster.test_setup.Failures.test_cluster_destroy_failure
    """