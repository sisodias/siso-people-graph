"""The truth contract every response carries.

A result that says "3 works" is a lie if the query stopped at a limit of 3, and
an honest system cannot let a caller mistake a page for a corpus. Every response
therefore declares:

  * which source snapshots it saw, and where they were on this machine
  * what identity resolution was applied, and in which mode
  * total matched vs returned, and whether truncation occurred
  * rights state where the source declares one
  * every capability that was missing and might have changed the answer

The rule from the lane spec: no query may say "all" without a declared source
universe. `total_matched` is a real COUNT against the same predicate as the page
query -- not len(rows), which is what made the old works() unable to distinguish
5 results from 200-of-40,000.
"""
from __future__ import annotations

from dataclasses import dataclass, field

SCHEMA_VERSION = "people-graph-query-0.1"


@dataclass
class Page:
    """Counts that make truncation impossible to hide."""

    returned: int = 0
    total_matched: int | None = None
    limit: int | None = None
    offset: int = 0

    @property
    def truncated(self) -> bool:
        if self.total_matched is None:
            # Unknown total: assume truncation iff we filled the page exactly.
            return self.limit is not None and self.returned >= self.limit
        return self.returned + self.offset < self.total_matched

    def as_dict(self) -> dict:
        return {
            "returned": self.returned,
            "total_matched": self.total_matched,
            "limit": self.limit,
            "offset": self.offset,
            "truncated": self.truncated,
            "counts_are_exact": self.total_matched is not None,
        }


@dataclass
class Response:
    query_type: str
    query: dict
    result: dict = field(default_factory=dict)
    page: Page = field(default_factory=Page)
    capabilities: dict = field(default_factory=dict)
    sources: dict = field(default_factory=dict)
    identity: dict = field(default_factory=dict)
    coverage_gaps: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    execution: dict = field(default_factory=dict)

    def gap(self, text: str) -> None:
        if text not in self.coverage_gaps:
            self.coverage_gaps.append(text)

    def warn(self, text: str) -> None:
        if text not in self.warnings:
            self.warnings.append(text)

    def as_dict(self) -> dict:
        return {
            "schema_version": SCHEMA_VERSION,
            "query_type": self.query_type,
            "query": self.query,
            "result": self.result,
            "page": self.page.as_dict(),
            "identity_resolution": self.identity,
            "sources": self.sources,
            "capabilities": self.capabilities,
            "coverage_gaps": self.coverage_gaps,
            "warnings": self.warnings,
            "execution": self.execution,
        }
