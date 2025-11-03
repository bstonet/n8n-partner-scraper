from typing import Dict


def _score_by_keywords(text: str, keywords: Dict[str, int]) -> int:
    t = text.lower()
    score = 0
    for kw, pts in keywords.items():
        if kw in t:
            score += pts
    return score


def score_signals(text: str) -> Dict:
    t = text.lower()

    size = _score_by_keywords(
        t,
        {
            "careers": 6,
            "hiring": 5,
            "global": 4,
            "offices": 4,
            "100+": 3,
            "200+": 3,
            "employees": 2,
        },
    )
    size = min(size, 25)

    enterprise = _score_by_keywords(
        t,
        {
            "soc2": 6,
            "iso27001": 6,
            "sso": 3,
            "saml": 3,
            "okta": 2,
            "azure ad": 2,
            "sla": 2,
            "slas": 2,
            "siem": 2,
            "kubernetes": 2,
            "k8s": 2,
            "snowflake": 2,
            "databricks": 2,
            "terraform": 2,
        },
    )
    enterprise = min(enterprise, 25)

    tech = _score_by_keywords(
        t,
        {
            "kafka": 4,
            "dbt": 3,
            "airflow": 3,
            "snowflake": 3,
            "llm": 3,
            "rag": 2,
            "agent": 2,
            "orchestration": 2,
            "aws": 2,
            "gcp": 2,
            "azure": 2,
        },
    )
    tech = min(tech, 15)

    regulated = _score_by_keywords(
        t,
        {
            "healthcare": 3,
            "hipaa": 3,
            "fintech": 3,
            "banking": 3,
            "insurance": 3,
            "pharma": 3,
            "government": 3,
            "industrial": 2,
            "manufacturing": 2,
        },
    )
    regulated = min(regulated, 15)

    delivery = _score_by_keywords(
        t,
        {
            "statement of work": 3,
            "sow": 3,
            "managed services": 4,
            "24/7": 3,
            "24x7": 3,
            "support": 2,
            "sla": 2,
            "msp": 2,
        },
    )
    delivery = min(delivery, 15)

    marketing = _score_by_keywords(
        t,
        {
            "case studies": 4,
            "whitepaper": 3,
            "whitepapers": 3,
            "ebook": 2,
            "webinar": 2,
            "roi": 1,
        },
    )
    marketing = min(marketing, 10)

    total = size + enterprise + tech + regulated + delivery + marketing
    if total >= 70:
        tier = "Enterprise"
    elif total >= 50:
        tier = "Mid-market"
    else:
        tier = "SMB"

    return {
        "tier": tier,
        "total": total,
        "components": {
            "size_signals": size,
            "enterprise_security": enterprise,
            "tech_stack": tech,
            "regulated_verticals": regulated,
            "delivery_maturity": delivery,
            "marketing_assets": marketing,
        },
    }


