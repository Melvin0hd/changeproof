"""Bounded provider transport. Construction and dry runs never send requests."""
import json
import re
import urllib.request
import urllib.error

NEBIUS_URL = 'https://api.tokenfactory.nebius.com/v1/chat/completions'
MODELS_URL = 'https://api.tokenfactory.nebius.com/v1/models'
MODEL = 'nvidia/Nemotron-3_5-Lightning'
TAVILY_URL = 'https://api.tavily.com/search'
MAX_BYTES = 262144


def credential(value):
    if not isinstance(value, str) or not value:
        raise ValueError('missing_credential')
    if any(ch in value for ch in '\r\n'):
        raise ValueError('credential_contains_linebreak')
    normalized = value.strip(' \t')
    if not normalized:
        raise ValueError('missing_credential')
    if any(ord(ch) < 33 or ord(ch) > 126 for ch in normalized):
        raise ValueError('credential_contains_invalid_character')
    return normalized


def redact(value, key):
    if isinstance(value, dict):
        return {redact(k, key): redact(v, key) for k, v in value.items()
                if re.sub('[^a-z]', '', k.lower()) not in {
                    'authorization', 'apikey', 'token', 'headers', 'password', 'secret',
                    'requestheaders', 'responseheaders', 'cookie', 'setcookie'}}
    if isinstance(value, list):
        return [redact(v, key) for v in value]
    if isinstance(value, str):
        value = value.replace(key, '[REDACTED]')
        value = re.sub(r'(?im)authorization\s*[:=][^\r\n]*', '[REDACTED HEADER]', value)
        return re.sub(r'(?i)(?:bearer\s+|v1\.)[A-Za-z0-9_.-]+', '[REDACTED]', value)
    return value


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        return None


def send_json(url, body, key, *, authorized=False, timeout=30, opener=None, method='POST'):
    key = credential(key)
    if (url, method) not in {(NEBIUS_URL, 'POST'), (TAVILY_URL, 'POST'), (MODELS_URL, 'GET')}:
        raise ValueError('endpoint_not_allowed')
    if isinstance(timeout, bool) or not isinstance(timeout, (int, float)) or not 0 < timeout <= 60:
        raise ValueError('invalid_timeout')
    encoded = json.dumps(body, allow_nan=False).encode('utf-8') if method == 'POST' else b''
    if len(encoded) > MAX_BYTES:
        raise ValueError('request_too_large')
    if not authorized:
        return {'status': 'DRY_RUN', 'url': url, 'method': method,
                'content_type': 'application/json', 'content_length': len(encoded),
                'body_keys': sorted(body), 'provider_calls': 0}
    headers = {'Authorization': 'Bearer ' + key, 'Accept': 'application/json'}
    if method == 'POST':
        headers.update({'Content-Type': 'application/json', 'Content-Length': str(len(encoded))})
    request = urllib.request.Request(url, data=encoded if method == 'POST' else None,
                                     method=method, headers=headers)
    # No retries, redirects, ambient proxy, or fallback endpoints.
    transport = opener or urllib.request.build_opener(urllib.request.ProxyHandler({}), NoRedirect())
    try:
        with transport.open(request, timeout=timeout) as response:
            status = response.status
            raw = response.read(MAX_BYTES + 1)
        if len(raw) > MAX_BYTES:
            return {'status': 'FAILED', 'http_status': status, 'error': 'response_too_large'}
        result = json.loads(raw)
        if not isinstance(result, dict):
            raise ValueError('response_not_object')
        return {'status': 'RECEIVED', 'http_status': status, 'response': redact(result, key)}
    except urllib.error.HTTPError as error:
        try:
            raw = error.read(8193)
            if len(raw) > 8192:
                detail = '[OMITTED: oversized body]'
            else:
                text = raw.decode('utf-8', errors='replace')
                try:
                    detail = json.loads(text)
                except ValueError:
                    detail = text
        except Exception:
            detail = '[OMITTED: unreadable body]'
        return {'status': 'FAILED', 'http_status': error.code,
                'response_body': redact(detail, key), 'retry_performed': False}
    except Exception as error:
        return {'status': 'FAILED', 'error': type(error).__name__, 'retry_performed': False}


class NebiusClient:
    def __init__(self, key, *, url=NEBIUS_URL, model=MODEL, opener=None, timeout=30):
        self.key = credential(key)
        if url != NEBIUS_URL or not isinstance(model, str) or not re.fullmatch(r'nvidia/[A-Za-z0-9_.-]+', model):
            raise ValueError('unapproved_endpoint_or_model')
        self.url, self.model, self.opener, self.timeout = url, model, opener, timeout

    def complete(self, prompt, *, max_tokens=64, temperature=0, authorized=False, structured=False):
        if type(max_tokens) is not int or not 1 <= max_tokens <= 1200:
            raise ValueError('invalid_token_limit')
        if not isinstance(prompt, str) or not prompt or len(prompt) > 100000:
            raise ValueError('invalid_prompt')
        if not isinstance(temperature, (float, int)) or isinstance(temperature, bool) or not 0 <= temperature <= 2:
            raise ValueError('invalid_temperature')
        body = {'model': self.model, 'messages': [
            {'role': 'user', 'content': prompt}], 'max_tokens': max_tokens,
            'temperature': temperature}
        if structured:
            # Nebius documents extra_body as its extension container. Backend
            # support for NVIDIA's thinking flag must still be verified live.
            body.update({'response_format': {'type': 'json_object'},
                         'extra_body': {'chat_template_kwargs': {'enable_thinking': False}}})
        outcome = send_json(self.url, body, self.key, authorized=authorized,
            timeout=self.timeout, opener=self.opener)
        if outcome['status'] != 'RECEIVED':
            return outcome
        response = outcome.pop('response')
        observed = {'http_status': outcome['http_status'], 'model': response.get('model'),
                    'usage': response.get('usage'), 'content': None,
                    'finish_reason': None, 'reasoning_tokens': None,
                    'retry_performed': False}
        usage = response.get('usage')
        if isinstance(usage, dict) and isinstance(usage.get('completion_tokens_details'), dict):
            observed['reasoning_tokens'] = usage['completion_tokens_details'].get('reasoning_tokens')
        try:
            choice = response['choices'][0]
            observed['finish_reason'] = choice.get('finish_reason')
            content = choice['message']['content']
            observed['content'] = content
            if observed['finish_reason'] != 'stop':
                return dict(observed, status='FAILED', error='generation_not_completed')
            if not isinstance(content, str) or not content.strip():
                raise ValueError('missing_content')
            if response.get('model') != self.model:
                raise ValueError('unexpected_model')
            def reject_constant(value):
                raise ValueError('non_finite_json_number')
            parsed = json.loads(content, parse_constant=reject_constant)
            if not isinstance(parsed, dict):
                raise ValueError('content_not_object')
        except (KeyError, IndexError, TypeError, ValueError, AttributeError):
            return dict(observed, status='FAILED', error='invalid_model_response')
        return dict(observed, status='SUCCESS',
                    usage_available=isinstance(response.get('usage'), dict), result=parsed)
