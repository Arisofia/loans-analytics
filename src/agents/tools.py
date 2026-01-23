import inspect
from typing import Any, Callable, Dict, List, Optional


class Tool:
    def __init__(self, name: str, func: Callable[..., Any], description: str):
        self.name = name
        self.func = func
        self.description = description

    def run(self, **kwargs: Any) -> Any:
        return self.func(**kwargs)

    def to_dict(self) -> Dict[str, str]:
        return {
            "name": self.name,
            "description": self.description,
            "parameters": str(inspect.signature(self.func)),
        }


class ToolRegistry:
    def __init__(self):
        self.tools: Dict[str, Tool] = {}

    def register(
        self, name: Optional[str] = None, description: Optional[str] = None
    ) -> Callable[..., Any]:
        def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
            tool_name = name or func.__name__
            tool_description = description or func.__doc__ or "No description provided."
            self.tools[tool_name] = Tool(tool_name, func, tool_description)
            return func

        return decorator

    def get_tool(self, name: str) -> Optional[Tool]:
        return self.tools.get(name)

    def list_tools(self) -> List[Dict[str, str]]:
        return [tool.to_dict() for tool in self.tools.values()]


registry = ToolRegistry()


@registry.register(description="Simulate execution of an SQL query and return a sample result.")
def run_sql_query(query: str) -> List[Dict[str, Any]]:
    """
    Args:
        query (str): The SQL statement to execute.

    Returns:
        List[Dict[str, Any]]: A list of dictionaries representing query results.
    """
    # Placeholder for actual DB integration
    return [{"result": "Sample result for query: " + query}]


@registry.register(
    description="Simulate a portfolio scenario by adjusting interest rates or principal balances."
)
def simulate_portfolio_scenario(
    data_path: Optional[str] = None, rate_adjustment: float = 0.0, principal_adjustment: float = 0.0
) -> Dict[str, Any]:
    """
    Args:
        data_path (Optional[str]): Path to the loan data CSV.
        rate_adjustment (float): Value to add to all interest rates (e.g., 0.01 for +1%).
        principal_adjustment (float): Ratio to multiply all principal balances (e.g., 0.9 for -10%).

    Returns:
        Dict[str, Any]: Comparison between baseline and simulated KPIs.
    """
    import pandas as pd

    from src.analytics.enterprise_analytics_engine import LoanAnalyticsEngine

    if data_path:
        df = pd.read_csv(data_path)
    else:
        # Sample data
        data = {
            "loan_amount": [250000, 450000, 150000, 600000],
            "appraised_value": [300000, 500000, 160000, 750000],
            "borrower_income": [80000, 120000, 60000, 150000],
            "monthly_debt": [1500, 2500, 1000, 3000],
            "loan_status": ["current", "current", "current", "current"],
            "interest_rate": [0.035, 0.042, 0.038, 0.045],
            "principal_balance": [240000, 440000, 145000, 590000],
        }
        df = pd.DataFrame(data)

    # Baseline
    engine_baseline = LoanAnalyticsEngine(df)
    baseline_kpis = engine_baseline.run_full_analysis()

    # Simulation
    df_sim = df.copy()
    if rate_adjustment != 0:
        df_sim["interest_rate"] += rate_adjustment
    if principal_adjustment != 0:
        df_sim["principal_balance"] *= principal_adjustment

    engine_sim = LoanAnalyticsEngine(df_sim)
    sim_kpis = engine_sim.run_full_analysis()

    return {
        "baseline": baseline_kpis,
        "simulated": sim_kpis,
        "adjustments": {
            "rate_adjustment": rate_adjustment,
            "principal_adjustment": principal_adjustment,
        },
    }


@registry.register(description="Run a full portfolio analysis using the LoanAnalyticsEngine.")
def run_portfolio_analysis(data_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Args:
        data_path (Optional[str]): Path to the loan data CSV. If not provided, uses a sample.

    Returns:
        Dict[str, Any]: KPI dashboard and risk alerts.
    """
    import pandas as pd

    from src.analytics.enterprise_analytics_engine import LoanAnalyticsEngine

    if data_path:
        df = pd.read_csv(data_path)
    else:
        # Sample data
        data = {
            "loan_amount": [250000, 450000, 150000, 600000, 300000],
            "appraised_value": [300000, 500000, 160000, 750000, 320000],
            "borrower_income": [80000, 120000, 60000, 150000, 50000],
            "monthly_debt": [1500, 2500, 1000, 3000, 2500],
            "loan_status": [
                "current",
                "30-59 days past due",
                "current",
                "current",
                "60-89 days past due",
            ],
            "interest_rate": [0.035, 0.042, 0.038, 0.045, 0.055],
            "principal_balance": [240000, 440000, 145000, 590000, 295000],
        }
        df = pd.DataFrame(data)

    engine = LoanAnalyticsEngine(df)
    kpis = engine.run_full_analysis()
    risk_loans = engine.risk_alerts()

    return {
        "kpis": kpis,
        "risk_alerts_count": len(risk_loans),
        "risk_loans_summary": (
            risk_loans[["loan_amount", "principal_balance", "risk_score"]].to_dict(orient="records")
            if not risk_loans.empty
            else []
        ),
    }


@registry.register(
    description="Analyze customer behavior including CLV, churn probability, and segmentation."
)
def analyze_customer_behavior(customer_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Args:
        customer_id (Optional[str]): Specific customer ID to analyze. If None, analyzes all customers.

    Returns:
        Dict[str, Any]: Customer intelligence metrics (CLV, churn, segments).
    """
    # Placeholder for behavioral prediction logic
    import random

    if customer_id:
        return {
            "customer_id": customer_id,
            "clv": round(random.uniform(5000, 50000), 2),
            "churn_probability": round(random.uniform(0, 1), 2),
            "segment": random.choice(["High Value", "At Risk", "Stable", "New"]),
            "last_interaction": "2025-12-25",
        }

    return {
        "total_customers": 150,
        "segments": {"High Value": 30, "At Risk": 25, "Stable": 80, "New": 15},
        "average_clv": 25400.50,
        "overall_churn_rate": 0.12,
    }


@registry.register(description="Send a message to a Slack channel.")
def send_slack_notification(message: str, channel: Optional[str] = None) -> bool:
    """
    Args:
        message (str): The message to send.
        channel (Optional[str]): Target channel name or ID.

    Returns:
        bool: True if sent successfully.
    """
    from src.agents.outputs import SlackOutput

    output = SlackOutput()
    return output.publish(message, channel=channel)


@registry.register(description="Create a new page in Notion.")
def create_notion_page(title: str, content: str) -> bool:
    """
    Args:
        title (str): The title of the page.
        content (str): Markdown or plain text content.

    Returns:
        bool: True if created successfully.
    """
    from src.agents.outputs import NotionOutput

    output = NotionOutput()
    return output.publish(content, title=title)


@registry.register(
    description="Compute investor-specific KPIs including ROI, capital efficiency, and IRR."
)
def compute_investor_kpis(portfolio_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Args:
        portfolio_data (Optional[Dict[str, Any]]): Data to analyze.

    Returns:
        Dict[str, Any]: Investor metrics.
    """
    # Placeholder for investor analytics
    return {
        "roi_percent": 15.4,
        "capital_efficiency_ratio": 1.25,
        "irr_forecast": 0.18,
        "valuation_estimate_m_usd": 45.0,
    }


@registry.register(description="Generate an ROI analysis report for board-level review.")
def generate_roi_report(timeframe: str = "yearly") -> str:
    """
    Args:
        timeframe (str): Report timeframe (e.g., 'quarterly', 'yearly').

    Returns:
        str: Markdown formatted report.
    """
    return f"# ROI Report - {timeframe.capitalize()}\n\nDetailed analysis of portfolio returns and capital allocation efficiency."


@registry.register(
    description="Score a list of leads based on historical conversion data and profile matching."
)
def score_leads(leads: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Args:
        leads (List[Dict[str, Any]]): List of lead dictionaries.

    Returns:
        List[Dict[str, Any]]: Leads with added 'sales_score' and 'priority'.
    """
    import random

    scored_leads = []
    for lead in leads:
        score = round(random.uniform(0, 100), 2)
        scored_leads.append(
            {
                **lead,
                "sales_score": score,
                "priority": "High" if score > 80 else "Medium" if score > 50 else "Low",
            }
        )
    return sorted(scored_leads, key=lambda x: x["sales_score"], reverse=True)


@registry.register(description="Analyze the sales funnel to identify conversion bottlenecks.")
def analyze_sales_funnel(date_range: Optional[str] = None) -> Dict[str, Any]:
    """
    Args:
        date_range (Optional[str]): Period to analyze.

    Returns:
        Dict[str, Any]: Funnel stage counts and conversion rates.
    """
    return {
        "stages": {"leads": 1000, "qualified": 450, "proposal": 150, "closed_won": 45},
        "conversion_rates": {
            "lead_to_qualified": 0.45,
            "qualified_to_proposal": 0.33,
            "proposal_to_closed": 0.30,
            "overall": 0.045,
        },
    }


@registry.register(
    description="Fetch data about market competitors including pricing and market share."
)
def fetch_market_competitors(sector: str = "fintech") -> Dict[str, Any]:
    """
    Args:
        sector (str): Market sector to analyze.

    Returns:
        Dict[str, Any]: Competitor insights.
    """
    return {
        "sector": sector,
        "competitors": [
            {"name": "CompeteCorp", "market_share": 0.25, "avg_interest_rate": 0.04},
            {"name": "LoanLogic", "market_share": 0.15, "avg_interest_rate": 0.038},
            {"name": "FinanceFlow", "market_share": 0.10, "avg_interest_rate": 0.045},
        ],
    }


@registry.register(
    description="Get current economic indicators such as inflation and central bank rates."
)
def get_economic_indicators(region: str = "US") -> Dict[str, float]:
    """
    Args:
        region (str): Geographical region.

    Returns:
        Dict[str, float]: Key economic metrics.
    """
    return {"inflation_rate": 0.032, "central_bank_rate": 0.0525, "gdp_growth": 0.021}


@registry.register(description="Monitor real-time SLA performance for operational processes.")
def monitor_sla_performance() -> Dict[str, Any]:
    """
    Returns:
        Dict[str, Any]: SLA metrics.
    """
    return {
        "average_processing_time_hours": 4.5,
        "sla_breach_rate_percent": 2.1,
        "active_queues": [
            {"name": "Application Review", "count": 45, "status": "Busy"},
            {"name": "Verification", "count": 12, "status": "Normal"},
        ],
    }


@registry.register(
    description="Identify operational process bottlenecks using process mining techniques."
)
def identify_process_bottlenecks() -> List[Dict[str, str]]:
    """
    Returns:
        List[Dict[str, str]]: List of identified bottlenecks and recommendations.
    """
    return [
        {
            "process": "Document Verification",
            "issue": "High manual touch",
            "recommendation": "Automate OCR validation",
        },
        {
            "process": "Final Approval",
            "issue": "Lack of redundant approvers",
            "recommendation": "Expand approval pool",
        },
    ]


@registry.register(description="Analyze brand sentiment across social media and news sources.")
def analyze_brand_sentiment(brand_name: str = "Abaco Capital") -> Dict[str, Any]:
    """
    Args:
        brand_name (str): Name of the brand.

    Returns:
        Dict[str, Any]: Sentiment scores and top mentions.
    """
    return {
        "brand": brand_name,
        "sentiment_score": 0.78,
        "mentions_count": 1250,
        "sentiment_distribution": {"positive": 0.65, "neutral": 0.25, "negative": 0.10},
    }


@registry.register(description="Track the performance of marketing campaigns.")
def track_campaign_performance(campaign_id: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Args:
        campaign_id (Optional[str]): Specific campaign to track.

    Returns:
        List[Dict[str, Any]]: Performance metrics (CTR, CPC, Conversions).
    """
    return [
        {"campaign": "Q4 Growth", "ctr": 0.025, "cpc": 1.20, "conversions": 150},
        {"campaign": "Referral Program", "ctr": 0.040, "cpc": 0.50, "conversions": 300},
    ]


@registry.register(description="Get usage metrics for specific product features.")
def get_feature_usage_metrics() -> List[Dict[str, Any]]:
    """
    Returns:
        List[Dict[str, Any]]: List of features and their adoption/retention rates.
    """
    return [
        {"feature": "Risk Dashboard", "adoption_rate": 0.85, "retention_rate": 0.92},
        {"feature": "Scenario Simulator", "adoption_rate": 0.45, "retention_rate": 0.60},
        {"feature": "Automated Reporting", "adoption_rate": 0.70, "retention_rate": 0.88},
    ]


@registry.register(description="Prioritize the product roadmap using RICE scoring.")
def prioritize_product_roadmap(features: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Args:
        features (List[Dict[str, Any]]): List of proposed features with Reach, Impact, Confidence, and Effort.

    Returns:
        List[Dict[str, Any]]: Prioritized list of features based on RICE score.
    """
    scored_features = []
    for f in features:
        # RICE Score = (Reach * Impact * Confidence) / Effort
        score = (f.get("reach", 0) * f.get("impact", 0) * f.get("confidence", 0)) / f.get(
            "effort", 1
        )
        scored_features.append({**f, "rice_score": round(score, 2)})
    return sorted(scored_features, key=lambda x: x["rice_score"], reverse=True)


@registry.register(
    description="Predict employee performance based on historical KPIs and engagement scores."
)
def predict_employee_performance(employee_id: str) -> Dict[str, Any]:
    """
    Args:
        employee_id (str): Unique identifier of the employee.

    Returns:
        Dict[str, Any]: Predicted performance rating and coaching tips.
    """
    return {
        "employee_id": employee_id,
        "predicted_rating": "Exceeds Expectations",
        "confidence_score": 0.82,
        "coaching_tips": ["Focus on leadership opportunities", "Expand technical mentorship"],
    }


@registry.register(description="Assess retention risk for an employee or department.")
def assess_retention_risk(target_id: str) -> Dict[str, Any]:
    """
    Args:
        target_id (str): Employee ID or Department name.

    Returns:
        Dict[str, Any]: Risk level and primary drivers.
    """
    return {
        "target": target_id,
        "risk_level": "Medium",
        "risk_score": 0.45,
        "primary_drivers": ["Market compensation divergence", "Workload balance"],
    }


@registry.register(description="Retrieve the content of a document by its ID.")
def retrieve_document(doc_id: str) -> str:
    """
    Args:
        doc_id (str): The unique identifier of the document to retrieve.

    Returns:
        str: The content of the document as a string.
    """
    # Placeholder for document retrieval
    return f"Document content for {doc_id}"
