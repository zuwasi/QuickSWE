import os
import sys
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.raft import RaftNode, RaftCluster, NodeState


class TestBasicRaft:
    """Tests that should pass both before and after the fix."""

    @pytest.mark.pass_to_pass
    def test_leader_election(self):
        cluster = RaftCluster(["n1", "n2", "n3"])
        assert cluster.elect_leader("n1")
        assert cluster.nodes["n1"].state == NodeState.LEADER

    @pytest.mark.pass_to_pass
    def test_client_request_appends_to_log(self):
        cluster = RaftCluster(["n1", "n2", "n3"])
        cluster.elect_leader("n1")
        leader = cluster.nodes["n1"]
        idx = leader.client_request("SET x=1")
        assert idx == 1
        assert len(leader.log) == 1

    @pytest.mark.pass_to_pass
    def test_full_replication_commits(self):
        """With full replication to all nodes, entry should commit."""
        cluster = RaftCluster(["n1", "n2", "n3"])
        cluster.elect_leader("n1")
        leader = cluster.nodes["n1"]
        leader.client_request("SET x=1")
        cluster.replicate("n1")
        assert leader.commit_index >= 1


class TestMajorityCommit:
    """Tests that should fail before the fix and pass after."""

    @pytest.mark.fail_to_pass
    def test_no_commit_with_single_ack(self):
        """In a 5-node cluster, one ACK should NOT commit."""
        cluster = RaftCluster(["n1", "n2", "n3", "n4", "n5"])
        cluster.elect_leader("n1")
        leader = cluster.nodes["n1"]

        leader.client_request("SET x=1")

        # Partition leader from all but one follower
        for nid in ["n3", "n4", "n5"]:
            cluster.partition("n1", nid)

        cluster.replicate("n1")

        # Only n2 ACKed. Leader + n2 = 2, need 3 for majority in 5-node cluster
        assert leader.commit_index == 0, (
            f"Entry should NOT be committed with only 1 follower ACK in 5-node cluster, "
            f"but commit_index={leader.commit_index}"
        )

    @pytest.mark.fail_to_pass
    def test_commit_only_after_majority(self):
        """Entry should commit only after majority ACKs."""
        cluster = RaftCluster(["n1", "n2", "n3", "n4", "n5"])
        cluster.elect_leader("n1")
        leader = cluster.nodes["n1"]

        leader.client_request("CMD_A")

        # First: replicate to only 1 follower
        for nid in ["n3", "n4", "n5"]:
            cluster.partition("n1", nid)
        cluster.replicate("n1")
        assert leader.commit_index == 0, "Should not commit with 1 ACK"

        # Now allow one more follower
        cluster.heal_partition("n1", "n3")
        cluster.replicate("n1")
        # Leader + n2 + n3 = 3 >= majority(5)=3 -> should commit now
        assert leader.commit_index == 1, (
            f"Should commit after reaching majority, got commit_index={leader.commit_index}"
        )

    @pytest.mark.fail_to_pass
    def test_five_node_two_acks_not_enough(self):
        """In a 5-node cluster with 2 follower ACKs (3 total with leader), need 3 = majority.
        But with only 1 follower ACK (2 total), should NOT commit."""
        cluster = RaftCluster(["n1", "n2", "n3", "n4", "n5"])
        cluster.elect_leader("n1")
        leader = cluster.nodes["n1"]

        leader.client_request("CMD_X")
        leader.client_request("CMD_Y")

        # Only allow n2 to communicate (1 follower ACK)
        for nid in ["n3", "n4", "n5"]:
            cluster.partition("n1", nid)
        cluster.replicate("n1")

        # Leader + n2 = 2, majority of 5 = 3 -> should NOT commit
        assert leader.commit_index == 0, (
            f"2 nodes (leader + 1 follower) is not majority of 5, "
            f"but commit_index={leader.commit_index}"
        )

    @pytest.mark.fail_to_pass
    def test_multiple_entries_commit_correctly(self):
        """Multiple entries should each require majority for commit."""
        cluster = RaftCluster(["n1", "n2", "n3", "n4", "n5"])
        cluster.elect_leader("n1")
        leader = cluster.nodes["n1"]

        leader.client_request("CMD_1")
        leader.client_request("CMD_2")

        # Only 1 follower can communicate
        for nid in ["n3", "n4", "n5"]:
            cluster.partition("n1", nid)
        cluster.replicate("n1")

        assert leader.commit_index == 0, "Should not commit with minority"

        # Allow majority
        cluster.heal_partition("n1", "n3")
        cluster.heal_partition("n1", "n4")
        cluster.replicate("n1")

        assert leader.commit_index == 2, (
            f"Both entries should commit with majority, got {leader.commit_index}"
        )
        assert len(leader.applied_commands) == 2
