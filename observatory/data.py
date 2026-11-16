"""Read only GitHub's publicly visible calendar, without credentials."""
from datetime import date, datetime, timedelta, timezone
from html.parser import HTMLParser
from urllib.request import Request, urlopen
from urllib.error import URLError
from time import sleep
import re


class CalendarParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.cells = {}
        self.tips = {}
        self.current = None

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == 'td' and 'data-date' in a and 'data-level' in a:
            if a.get('id') in self.cells:
                raise ValueError('duplicate calendar cell')
            self.cells[a['id']] = (a['data-date'], a['data-level'])
        if tag == 'tool-tip' and a.get('for', '').startswith('contribution-day-component-'):
            self.current = a['for']

    def handle_data(self, value):
        if self.current:
            self.tips[self.current] = self.tips.get(self.current, '') + value

    def handle_endtag(self, tag):
        if tag == 'tool-tip':
            self.current = None


def parse_calendar(html):
    parser = CalendarParser()
    parser.feed(html)
    days = []
    for key, (raw_date, raw_level) in parser.cells.items():
        day = date.fromisoformat(raw_date)
        level = int(raw_level)
        match = re.fullmatch(r'\s*(No|[\d,]+) contributions? on .+?\.\s*', parser.tips.get(key, ''))
        if not match or not 0 <= level <= 4:
            raise ValueError('malformed contribution calendar')
        count = 0 if match[1] == 'No' else int(match[1].replace(',', ''))
        if (count == 0) != (level == 0):
            raise ValueError('inconsistent contribution level')
        days.append((day, count, level))
    days.sort()
    if not 350 <= len(days) <= 372 or any(b[0] - a[0] != timedelta(days=1) for a, b in zip(days, days[1:])):
        raise ValueError('incomplete, empty, or discontinuous calendar')
    return days


def fetch_calendar():
    request = Request('https://github.com/users/AmirInit/contributions', headers={'User-Agent': 'AmirInit-Life-Observatory/1.0', 'Accept-Language': 'en-US,en;q=0.9'})
    for attempt in range(3):
        try:
            with urlopen(request, timeout=30) as response:
                payload = response.read(2_000_001)
            if len(payload) > 2_000_000:
                raise ValueError('calendar response exceeds size limit')
            days = parse_calendar(payload.decode('utf-8'))
            today = datetime.now(timezone.utc).date()
            if not today - timedelta(days=2) <= days[-1][0] <= today + timedelta(days=1):
                raise ValueError('calendar response is stale or future-dated')
            return days
        except (URLError, TimeoutError):
            if attempt == 2:
                raise
            sleep(attempt + 1)


def seed(days):
    first_sunday = days[0][0] - timedelta(days=(days[0][0].weekday() + 1) % 7)
    return {((day - first_sunday).days // 7, (day.weekday() + 1) % 7): level
            for day, count, level in days if count > 0}
