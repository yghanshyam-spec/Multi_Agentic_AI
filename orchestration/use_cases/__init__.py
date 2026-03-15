"""Use-case config registry — all 5 production use cases."""
from .incident_response           import INCIDENT_RESPONSE_CONFIG
from .content_generation          import CONTENT_GENERATION_CONFIG
from .invoice_to_pay              import INVOICE_TO_PAY_CONFIG
from .uc1_sales_intelligence      import UC1_SALES_INTELLIGENCE_CONFIG
from .uc2_employee_onboarding     import UC2_EMPLOYEE_ONBOARDING_CONFIG
from .uc3_procurement_exception   import UC3_PROCUREMENT_EXCEPTION_CONFIG
from .uc4_customer_support_desk   import UC4_CUSTOMER_SUPPORT_CONFIG
from .uc5_market_research_proposal import UC5_MARKET_RESEARCH_PROPOSAL_CONFIG

USE_CASE_REGISTRY = {
    "incident_response":        INCIDENT_RESPONSE_CONFIG,
    "content_generation":       CONTENT_GENERATION_CONFIG,
    "invoice_to_pay":           INVOICE_TO_PAY_CONFIG,
    "sales_intelligence":       UC1_SALES_INTELLIGENCE_CONFIG,
    "employee_onboarding":      UC2_EMPLOYEE_ONBOARDING_CONFIG,
    "procurement_exception":    UC3_PROCUREMENT_EXCEPTION_CONFIG,
    "customer_support_desk":    UC4_CUSTOMER_SUPPORT_CONFIG,
    "market_research_proposal": UC5_MARKET_RESEARCH_PROPOSAL_CONFIG,
}
