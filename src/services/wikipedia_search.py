"""Wikipedia and historical content search functionality."""

from typing import List, Dict, Any
from src.utils.logger import get_logger
from src.services.wikipedia_search_utils import get_mock_historical_stories
from src.services.wikipedia_parser import parse_wikipedia_content

logger = get_logger("wikipedia_search")


class WikipediaSearch:
    """Wikipedia and web-based historical content search."""

    def __init__(self, cache):
        """Initialize Wikipedia search with cache."""
        self.cache = cache

    def search_historical_stories(self, location: str, max_results: int = 3) -> List[Dict[str, Any]]:
        """Search for real historical stories and facts using Wikipedia API."""
        logger.info(f"Searching historical stories for: {location}")

        # Check cache first
        cache_key = f"history_{location}_{max_results}"
        cached = self.cache.get(cache_key)
        if cached:
            logger.info(f"Returning {len(cached)} cached historical results")
            return cached

        try:
            import wikipediaapi

            wiki = wikipediaapi.Wikipedia(language='en', user_agent='RouteStories/1.0')
            page = wiki.page(location)

            results = []
            if page.exists():
                logger.debug(f"Wikipedia page found: {page.title}")

                # Main article
                content = parse_wikipedia_content(page.summary, f"About {location}", page.fullurl)
                results.append(content)

                # Add sections as additional stories
                section_count = 0
                for section in page.sections:
                    if section_count >= max_results - 1:
                        break
                    try:
                        section_title = section.title
                        section_content = wiki.page(f"{location}#{section_title}").summary
                        if section_content and len(section_content) > 50:
                            content = parse_wikipedia_content(
                                section_content,
                                f"{location} - {section_title}",
                                f"{page.fullurl}#{section_title}"
                            )
                            results.append(content)
                            section_count += 1
                    except Exception:
                        continue

                logger.info(f"Found {len(results)} Wikipedia results for: {location}")

                if results:
                    self.cache.set(cache_key, results)
                    return results

            logger.debug(f"Wikipedia page not found for: {location}, using fallback")

        except ImportError:
            logger.warning("wikipediaapi not installed, using mock data")
            return get_mock_historical_stories(location, max_results)
        except Exception as e:
            logger.error(f"Wikipedia search failed: {e}")
            return get_mock_historical_stories(location, max_results)

        # Fallback to mock data
        return get_mock_historical_stories(location, max_results)

    def _search_web_historical(self, location: str, max_results: int = 3) -> List[Dict[str, Any]]:
        """Search web for historical content using DuckDuckGo."""
        try:
            from duckduckgo_search import DDGS

            results = []
            with DDGS() as ddgs:
                search_results = ddgs.text(f"{location} history", max_results=max_results)

                for result in search_results:
                    content = {
                        "title": result.get('title', 'Unknown'),
                        "content": result.get('body', '')[:500],
                        "source": "Web Search",
                        "url": result.get('href', ''),
                        "period": "Historical"
                    }
                    results.append(content)

            logger.info(f"Found {len(results)} web results for: {location}")
            return results if results else get_mock_historical_stories(location, max_results)

        except ImportError:
            logger.warning("duckduckgo_search not installed, using mock data")
            return get_mock_historical_stories(location, max_results)
        except Exception as e:
            logger.error(f"Web search failed: {e}")
            return get_mock_historical_stories(location, max_results)
