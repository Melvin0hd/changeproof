"""Bounded retrieval adapter, live execution disabled unless explicitly authorized."""
from datetime import datetime, timezone
from urllib.parse import urlsplit
from schemas import SearchEvidence
from provider_client import send_json, TAVILY_URL


class TavilyRetriever:
    def __init__(self, key, opener=None):
        self.key, self.opener = key, opener

    def search(self, query, *, authorized=False, include_domains=None):
        if not isinstance(query, str) or not query.strip() or len(query) > 500:
            raise ValueError('invalid_query')
        body = {'query': query, 'search_depth': 'basic',
                'max_results': 3, 'include_answer': False, 'include_raw_content': False}
        if include_domains is not None:
            if not isinstance(include_domains, list) or len(include_domains) != 1 or not isinstance(include_domains[0], str):
                raise ValueError('invalid_domain_filter')
            body['include_domains'] = include_domains
        result = send_json(TAVILY_URL, body,
            self.key, authorized=authorized, opener=self.opener)
        if result['status'] != 'RECEIVED':
            return result
        rows = result['response'].get('results')
        if not isinstance(rows, list) or len(rows) > 3:
            raise ValueError('invalid_retrieval_response')
        evidence = []
        for index, row in enumerate(rows):
            if not isinstance(row, dict):
                raise ValueError('invalid_source')
            url = row.get('url')
            if not isinstance(url, str) or urlsplit(url).scheme not in {'http', 'https'} or not urlsplit(url).hostname:
                raise ValueError('invalid_source_url')
            if not isinstance(row.get('content'), str) or not row['content']:
                raise ValueError('missing_source_text')
            evidence.append(SearchEvidence(query, 'retrieval_' + str(index + 1), url,
                row.get('title', ''), urlsplit(url).hostname, None,
                datetime.now(timezone.utc).isoformat(), row['content'],
                'search_excerpt_unverified', index + 1))
        return {'status': 'SUCCESS', 'evidence': evidence,
                'http_status': result['http_status'], 'provider_response': result['response']}
