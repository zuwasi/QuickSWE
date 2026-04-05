"""
Simplified Raft consensus protocol implementation.

Implements leader election, log replication, and commit tracking
for a cluster of nodes. Designed for correctness testing, not performance.
"""

from enum import Enum, auto
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple, Any
import random


class NodeState(Enum):
    FOLLOWER = auto()
    CANDIDATE = auto()
    LEADER = auto()


@dataclass
class LogEntry:
    term: int
    index: int
    command: Any
    committed: bool = False


@dataclass
class AppendEntriesRequest:
    term: int
    leader_id: str
    prev_log_index: int
    prev_log_term: int
    entries: List[LogEntry]
    leader_commit: int


@dataclass
class AppendEntriesResponse:
    term: int
    success: bool
    node_id: str
    match_index: int = 0


@dataclass
class RequestVoteRequest:
    term: int
    candidate_id: str
    last_log_index: int
    last_log_term: int


@dataclass
class RequestVoteResponse:
    term: int
    vote_granted: bool
    voter_id: str


class RaftNode:
    """A single Raft consensus node."""

    def __init__(self, node_id: str, cluster_size: int):
        self.node_id = node_id
        self.cluster_size = cluster_size

        # Persistent state
        self.current_term = 0
        self.voted_for: Optional[str] = None
        self.log: List[LogEntry] = []

        # Volatile state
        self.state = NodeState.FOLLOWER
        self.commit_index = 0
        self.last_applied = 0

        # Leader state
        self.next_index: Dict[str, int] = {}
        self.match_index: Dict[str, int] = {}
        self.votes_received: Set[str] = set()

        # Applied commands log (state machine)
        self.applied_commands: List[Any] = []

        # Election timeout tracking
        self.election_timeout = 0
        self.heartbeat_timeout = 0

    @property
    def last_log_index(self) -> int:
        return len(self.log)

    @property
    def last_log_term(self) -> int:
        if self.log:
            return self.log[-1].term
        return 0

    def _get_log_entry(self, index: int) -> Optional[LogEntry]:
        """Get log entry at 1-based index."""
        if 1 <= index <= len(self.log):
            return self.log[index - 1]
        return None

    def _get_log_term(self, index: int) -> int:
        entry = self._get_log_entry(index)
        return entry.term if entry else 0

    def become_leader(self):
        """Transition to leader state."""
        self.state = NodeState.LEADER
        self.next_index = {}
        self.match_index = {}
        # Leader's own match_index is its last log index
        self.match_index[self.node_id] = self.last_log_index

    def become_follower(self, term: int):
        """Transition to follower state."""
        self.state = NodeState.FOLLOWER
        self.current_term = term
        self.voted_for = None

    def become_candidate(self):
        """Transition to candidate state and start election."""
        self.state = NodeState.CANDIDATE
        self.current_term += 1
        self.voted_for = self.node_id
        self.votes_received = {self.node_id}

    def start_election(self) -> List[RequestVoteRequest]:
        """Start a new election. Returns vote requests to send."""
        self.become_candidate()
        return [RequestVoteRequest(
            term=self.current_term,
            candidate_id=self.node_id,
            last_log_index=self.last_log_index,
            last_log_term=self.last_log_term,
        )]

    def handle_vote_request(self, req: RequestVoteRequest) -> RequestVoteResponse:
        """Handle an incoming vote request."""
        if req.term < self.current_term:
            return RequestVoteResponse(
                term=self.current_term,
                vote_granted=False,
                voter_id=self.node_id,
            )

        if req.term > self.current_term:
            self.become_follower(req.term)

        vote_granted = False
        if self.voted_for in (None, req.candidate_id):
            # Check log is at least as up-to-date
            if (req.last_log_term > self.last_log_term or
                (req.last_log_term == self.last_log_term and
                 req.last_log_index >= self.last_log_index)):
                self.voted_for = req.candidate_id
                vote_granted = True

        return RequestVoteResponse(
            term=self.current_term,
            vote_granted=vote_granted,
            voter_id=self.node_id,
        )

    def handle_vote_response(self, resp: RequestVoteResponse) -> bool:
        """Handle vote response. Returns True if became leader."""
        if resp.term > self.current_term:
            self.become_follower(resp.term)
            return False

        if self.state != NodeState.CANDIDATE:
            return False

        if resp.vote_granted:
            self.votes_received.add(resp.voter_id)
            majority = (self.cluster_size // 2) + 1
            if len(self.votes_received) >= majority:
                self.become_leader()
                return True

        return False

    def client_request(self, command: Any) -> Optional[int]:
        """Handle a client request. Returns log index or None if not leader."""
        if self.state != NodeState.LEADER:
            return None

        entry = LogEntry(
            term=self.current_term,
            index=self.last_log_index + 1,
            command=command,
        )
        self.log.append(entry)
        self.match_index[self.node_id] = self.last_log_index
        return entry.index

    def prepare_append_entries(self, follower_id: str) -> AppendEntriesRequest:
        """Prepare AppendEntries RPC for a specific follower."""
        next_idx = self.next_index.get(follower_id, self.last_log_index + 1)
        prev_idx = next_idx - 1
        prev_term = self._get_log_term(prev_idx)

        entries = []
        for i in range(next_idx, self.last_log_index + 1):
            entry = self._get_log_entry(i)
            if entry:
                entries.append(LogEntry(
                    term=entry.term,
                    index=entry.index,
                    command=entry.command,
                ))

        return AppendEntriesRequest(
            term=self.current_term,
            leader_id=self.node_id,
            prev_log_index=prev_idx,
            prev_log_term=prev_term,
            entries=entries,
            leader_commit=self.commit_index,
        )

    def handle_append_entries(self, req: AppendEntriesRequest) -> AppendEntriesResponse:
        """Handle incoming AppendEntries RPC (as follower)."""
        if req.term < self.current_term:
            return AppendEntriesResponse(
                term=self.current_term,
                success=False,
                node_id=self.node_id,
            )

        if req.term >= self.current_term:
            self.become_follower(req.term)

        # Check prev log entry matches
        if req.prev_log_index > 0:
            prev_entry = self._get_log_entry(req.prev_log_index)
            if prev_entry is None or prev_entry.term != req.prev_log_term:
                return AppendEntriesResponse(
                    term=self.current_term,
                    success=False,
                    node_id=self.node_id,
                )

        # Append new entries
        for entry in req.entries:
            idx = entry.index
            if idx <= len(self.log):
                existing = self.log[idx - 1]
                if existing.term != entry.term:
                    self.log = self.log[:idx - 1]
                    self.log.append(LogEntry(
                        term=entry.term,
                        index=entry.index,
                        command=entry.command,
                    ))
            else:
                self.log.append(LogEntry(
                    term=entry.term,
                    index=entry.index,
                    command=entry.command,
                ))

        # Update commit index
        if req.leader_commit > self.commit_index:
            self.commit_index = min(req.leader_commit, self.last_log_index)
            self._apply_committed()

        return AppendEntriesResponse(
            term=self.current_term,
            success=True,
            node_id=self.node_id,
            match_index=self.last_log_index,
        )

    def handle_append_response(self, resp: AppendEntriesResponse):
        """Handle AppendEntries response (as leader)."""
        if resp.term > self.current_term:
            self.become_follower(resp.term)
            return

        if self.state != NodeState.LEADER:
            return

        if resp.success:
            self.match_index[resp.node_id] = resp.match_index
            self.next_index[resp.node_id] = resp.match_index + 1
            self._try_advance_commit()
        else:
            current_next = self.next_index.get(resp.node_id, self.last_log_index + 1)
            self.next_index[resp.node_id] = max(1, current_next - 1)

    def _try_advance_commit(self):
        """Try to advance the commit index based on match indices."""
        for n in range(self.commit_index + 1, self.last_log_index + 1):
            entry = self._get_log_entry(n)
            if entry is None or entry.term != self.current_term:
                continue

            # Count how many nodes have this entry
            for node_id, match_idx in self.match_index.items():
                if match_idx >= n:
                    self.commit_index = n
                    break

        self._apply_committed()

    def _apply_committed(self):
        """Apply committed but not yet applied entries to state machine."""
        while self.last_applied < self.commit_index:
            self.last_applied += 1
            entry = self._get_log_entry(self.last_applied)
            if entry:
                entry.committed = True
                self.applied_commands.append(entry.command)

    def get_committed_commands(self) -> List[Any]:
        """Return list of committed and applied commands."""
        return list(self.applied_commands)


class RaftCluster:
    """Simulates a Raft cluster for testing."""

    def __init__(self, node_ids: List[str]):
        self.nodes: Dict[str, RaftNode] = {}
        for nid in node_ids:
            self.nodes[nid] = RaftNode(nid, len(node_ids))
        self.partitioned: Set[Tuple[str, str]] = set()

    def can_communicate(self, from_id: str, to_id: str) -> bool:
        return (from_id, to_id) not in self.partitioned

    def partition(self, from_id: str, to_id: str):
        self.partitioned.add((from_id, to_id))
        self.partitioned.add((to_id, from_id))

    def heal_partition(self, from_id: str, to_id: str):
        self.partitioned.discard((from_id, to_id))
        self.partitioned.discard((to_id, from_id))

    def elect_leader(self, candidate_id: str) -> bool:
        """Force an election for the given candidate."""
        candidate = self.nodes[candidate_id]
        vote_reqs = candidate.start_election()

        for nid, node in self.nodes.items():
            if nid == candidate_id:
                continue
            if not self.can_communicate(candidate_id, nid):
                continue
            resp = node.handle_vote_request(vote_reqs[0])
            if candidate.handle_vote_response(resp):
                # Initialize next_index for all followers
                for fid in self.nodes:
                    if fid != candidate_id:
                        candidate.next_index[fid] = candidate.last_log_index + 1
                        candidate.match_index[fid] = 0
                return True

        return False

    def replicate(self, leader_id: str):
        """Send AppendEntries from leader to all followers and process responses."""
        leader = self.nodes[leader_id]
        if leader.state != NodeState.LEADER:
            return

        for nid, node in self.nodes.items():
            if nid == leader_id:
                continue
            if not self.can_communicate(leader_id, nid):
                continue

            req = leader.prepare_append_entries(nid)
            resp = node.handle_append_entries(req)
            if self.can_communicate(nid, leader_id):
                leader.handle_append_response(resp)
