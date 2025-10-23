from __future__ import annotations
from google.adk.agents import LlmAgent
from pydantic import BaseModel, Field
from typing import Optional

from .tools import (
    create_inquiry,
    get_inquiry_status,
    search_faq,
    initiate_return,
    get_order_inquiries,
)

GEMINI_MODEL = "gemini-2.5-flash"


class InquiryOutput(BaseModel):
    inquiry_id: str = Field(description="Inquiry ID")
    inquiry_type: str = Field(description="Type of inquiry")
    message: str = Field(description="Inquiry message")
    status: str = Field(description="Inquiry status")
    order_id: Optional[str] = Field(description="Related order ID", default="")
    created_at: Optional[str] = Field(description="Creation time", default="")
    response: Optional[str] = Field(description="Response message", default="")


root_agent = LlmAgent(
    name="customer_service_agent",
    instruction="""You are a customer service assistant. Your role is to help customers with inquiries, returns, refunds, and complaints.
    You can create inquiries, check inquiry status, search FAQ, initiate returns, and retrieve order-related inquiries.
    Always be helpful, clear, and professional.
    """,
    description="Handles customer support including returns, refunds, and inquiries",
    model=GEMINI_MODEL,
    tools=[
        create_inquiry,
        get_inquiry_status,
        search_faq,
        initiate_return,
        get_order_inquiries,
    ],
    output_schema=InquiryOutput,
    output_key="inquiry",
)
