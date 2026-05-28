from __future__ import annotations

from dataclasses import asdict, dataclass


NA = "N/A"


@dataclass
class Lead:
    business_name: str = NA
    category: str = NA
    address: str = NA
    contact_number: str = NA
    phone_type: str = NA
    whatsapp: str = NA
    email: str = NA
    website_url: str = NA
    website_status: str = "NO"
    instagram: str = NA
    facebook: str = NA
    google_maps_link: str = NA
    rating: str = NA
    review_count: str = NA
    source: str = NA

    def to_dict(self) -> dict:
        data = asdict(self)
        return {key: (value if value not in (None, "") else NA) for key, value in data.items()}

    def export_dict(self) -> dict:
        data = self.to_dict()
        return {
            "Business Name": data["business_name"],
            "Category": data["category"],
            "Address": data["address"],
            "Website Status": data["website_status"],
            "Website URL": data["website_url"],
            "Contact Number": data["contact_number"],
            "WhatsApp": data["whatsapp"],
            "Email": data["email"],
            "Instagram": data["instagram"],
            "Facebook": data["facebook"],
            "Google Maps Link": data["google_maps_link"],
            "Rating": data["rating"],
            "Review Count": data["review_count"],
        }
