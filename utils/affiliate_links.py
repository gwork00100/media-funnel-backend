import logging
import time
from datetime import datetime
from .supabase_client import supabase

def get_affiliate_link(
    link_id: str,
    fallback_url: str = None,
    utm_source: str = "autoloop",
    utm_medium: str = "affiliate",
    utm_campaign: str = "default_campaign"
) -> str:
    """
    Fetch the affiliate link from Supabase, inject UTM params, log click, or return fallback.
    """
    if not link_id:
        logging.info("No link_id provided, returning fallback URL.")
        return fallback_url

    try:
        # Fetch the affiliate URL from Supabase
        response = (
            supabase.table("affiliate_links")
            .select("url")
            .eq("link_id", link_id)
            .single()
            .execute()
        )
        data = response.data

        if data and "url" in data:
            url = data["url"]
        else:
            logging.info(f"Affiliate link not found for link_id={link_id}, using fallback.")
            url = fallback_url

        if not url:
            return fallback_url

        # Add UTM parameters
        separator = "&" if "?" in url else "?"
        url = f"{url}{separator}utm_source={utm_source}&utm_medium={utm_medium}&utm_campaign={utm_campaign}"

        # Log the click
        log_click(link_id, utm_source=utm_source, utm_medium=utm_medium, utm_campaign=utm_campaign)

        return url

    except Exception as e:
        logging.error(f"Error fetching affiliate link for link_id={link_id}: {e}")
        return fallback_url


def log_click(
    link_id: str,
    utm_source: str = "autoloop",
    utm_medium: str = "affiliate",
    utm_campaign: str = "default_campaign",
    max_retries: int = 3,
    delay: float = 1.0
) -> bool:
    """
    Logs a click to Supabase with retry on failure, including UTM info.
    """
    for attempt in range(max_retries):
        try:
            supabase.table("affiliate_clicks").insert({
                "link_id": link_id,
                "clicked_at": datetime.utcnow().isoformat(),
                "utm_source": utm_source,
                "utm_medium": utm_medium,
                "utm_campaign": utm_campaign
            }).execute()
            logging.info(f"Click logged for link_id={link_id}")
            return True
        except Exception as e:
            logging.error(f"Error logging click for link_id={link_id}: {e}")
            if attempt < max_retries - 1:
                time.sleep(delay)
            else:
                logging.warning(f"Failed to log click after {max_retries} attempts")
    return False
