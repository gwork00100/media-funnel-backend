import logging
from .supabase_client import supabase

def get_affiliate_link(link_id: str, fallback_url: str = None):
    """Fetch the affiliate link from Supabase or return fallback."""
    if not link_id:
        return fallback_url

    try:
        response = supabase.table("affiliate_links") \
                           .select("url") \
                           .eq("link_id", link_id) \
                           .single() \
                           .execute()
        data = response.data

        if data and "url" in data:
            return data["url"]
        else:
            logging.info(f"Affiliate link not found for link_id={link_id}, using fallback.")
            return fallback_url
    except Exception as e:
        logging.error(f"Error fetching affiliate link: {e}")
        return fallback_url
