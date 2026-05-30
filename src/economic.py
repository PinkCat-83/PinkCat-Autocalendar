"""
economic.py
Per-course economic calculations and annual income tax summary.
"""

from dataclasses import dataclass


@dataclass
class CourseSummary:
    name: str
    company: str
    hours_taught: float
    rate_per_hour: float
    withholding_pct: float

    @property
    def gross_total(self) -> float:
        return round(self.hours_taught * self.rate_per_hour, 2)

    @property
    def withholding_total(self) -> float:
        return round(self.gross_total * self.withholding_pct / 100, 2)

    @property
    def net_total(self) -> float:
        return round(self.gross_total - self.withholding_total, 2)

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "company": self.company,
            "hours_taught": self.hours_taught,
            "rate_per_hour": self.rate_per_hour,
            "withholding_pct": self.withholding_pct,
            "gross_total": self.gross_total,
            "withholding_total": self.withholding_total,
            "net_total": self.net_total,
        }


def calculate_annual_summary(summaries: list[CourseSummary]) -> dict:
    """
    Aggregates economic data across all courses.
    Returns annual totals and a breakdown by company (useful for tax filing).
    """
    by_company: dict[str, dict] = {}

    for s in summaries:
        company = s.company or "No company"
        if company not in by_company:
            by_company[company] = {
                "gross_total": 0.0,
                "withholding_total": 0.0,
                "net_total": 0.0,
                "courses": [],
            }
        by_company[company]["gross_total"] = round(
            by_company[company]["gross_total"] + s.gross_total, 2
        )
        by_company[company]["withholding_total"] = round(
            by_company[company]["withholding_total"] + s.withholding_total, 2
        )
        by_company[company]["net_total"] = round(
            by_company[company]["net_total"] + s.net_total, 2
        )
        by_company[company]["courses"].append(s.name)

    total_gross = round(sum(s.gross_total for s in summaries), 2)
    total_withholding = round(sum(s.withholding_total for s in summaries), 2)
    total_net = round(sum(s.net_total for s in summaries), 2)

    return {
        "total_gross": total_gross,
        "total_withholding": total_withholding,
        "total_net": total_net,
        "by_company": by_company,
    }
