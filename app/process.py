import os
from datetime import datetime
from typing import Dict

from .scrape_directory_json import scrape_directory_json
from .scrape_partner import scrape_partner
from .sheets import append_row


def process_all() -> Dict:
    directory = scrape_directory_json()
    domains = directory.get("domains", [])
    name_map = directory.get("name_map", {})

    counts = {"Enterprise": 0, "Mid-market": 0, "SMB": 0}

    for domain in domains:
        result = scrape_partner(domain, limit_pages=6)
        tier = result.get("tier", "SMB")
        if tier not in counts:
            tier = "SMB"
        counts[tier] += 1

        # Prepare row
        comps = result.get("score_components", {})
        row = {
            "timestamp": datetime.utcnow().isoformat(),
            "name": name_map.get(domain, ""),
            "domain": domain,
            "size_signals": comps.get("size_signals", 0),
            "enterprise_security": comps.get("enterprise_security", 0),
            "tech_stack": comps.get("tech_stack", 0),
            "regulated_verticals": comps.get("regulated_verticals", 0),
            "delivery_maturity": comps.get("delivery_maturity", 0),
            "marketing_assets": comps.get("marketing_assets", 0),
            "score_total": result.get("score_total", 0),
            "tier": tier,
            "sources": " ".join(result.get("sources", [])),
        }

        sheet_name = "Enterprise" if tier == "Enterprise" else ("MidMarket" if tier == "Mid-market" else "SMB")
        try:
            append_row(sheet_name, row)
        except Exception:
            # Allow running without Sheets configured
            pass

    return {
        "total": len(domains),
        "enterprise": counts["Enterprise"],
        "midmarket": counts["Mid-market"],
        "smb": counts["SMB"],
    }


