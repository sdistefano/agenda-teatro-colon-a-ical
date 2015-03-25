import BeautifulSoup, requests, icalendar, pytz
import re, datetime

SEASON_START_MONTH = 3      #Marzo
WRITE_AS_UTC = True             #google calendar

TZ_BuenosAires = pytz.timezone('America/Buenos_Aires')

DOMAIN = 'http://www.teatrocolon.org.ar'
BASE_URL = 'http://www.teatrocolon.org.ar/es/calendario'

class TeatroColonEvent(object):
    def __init__(self, name, section, start_time, url=None):
        self.name = name
        self.section = section
        self.start_time = start_time
        if url:
            self.url = DOMAIN + '/es' + url
        else:
            self.url = None

        if WRITE_AS_UTC:
            self.start_time = pytz.utc.normalize(self.start_time.astimezone(pytz.utc))

    def __repr__(self):
        return u'{}, {} {}'.format(self.name, self.section, self.start_time, self.url)

    @property
    def end_time(self):
        #no hay info en el sitio
        return self.start_time + datetime.timedelta(hours=2)

    def as_ical(self):
        event = icalendar.Event()
        event.add('summary', u'{} ({})'.format(self.name, self.section))
        event.add('dtstart', self.start_time)
        event.add('dtend', self.end_time)
        if self.url:
            event.add('description', self.url)

        return event


def _soup(url):
    if not url.startswith('http'):
        url = DOMAIN + url
    return BeautifulSoup.BeautifulSoup(requests.get(url).content)

def get_months():
    soup = _soup('http://www.teatrocolon.org.ar/es/calendario')
    out = []
    for li in soup.find('ul', {'class': 'menu', 'id': 'calendar'}).findAll('li'):
        link = li.find('a').get('href')
        #month_name = li.find('a').contents[0]
        out.append(link)

    return out

def _get_dt(month, day, time):
    rdate = re.compile('[^ ]* (?P<day>[0-9]*)')
    rtime = re.compile('([0-9]{1,2}).([0-9]{1,2})hs')
    day = int(rdate.match(day).groups()[0])
    time = rtime.match(time).groups()
    hour = int(time[0])
    #if 'pm' in time:
    #    hour += 12
    #if hour == 24:
    #    hour = 0
    minute = int(time[1])

    dt = datetime.datetime(year=datetime.date.today().year,
                         month=month,
                         day=day,
                         hour=hour,
                         minute=minute)
    return TZ_BuenosAires.localize(dt)

def fetch_events(month, url):
    soup = _soup(url)
    container = soup.find('div', {'class': 'item-page_calendario'})
    rows = container.find('table').findAll('tr')
    out = []
    for row in rows:
        tds = row.findAll('td')
        day, name, section, time = map(lambda x: x.text, tds)
        start_time = _get_dt(month, day, time)

        link = tds[1].find('a')
        if link:
            url = link.get('href')
            if url == '/':
                url = None

        out.append(TeatroColonEvent(name, section, start_time, url))
    return out

def main():
    events = []
    for n, link in enumerate(get_months()):
        month = SEASON_START_MONTH + n
        for event in fetch_events(month, link):
            events.append(event)

    f = file('colon-eventos-{}.ics'.format(datetime.date.today().year), 'wb')
    cal = icalendar.Calendar()
    for event in events:
        cal.add_component(event.as_ical())

    f.write(cal.to_ical())
    f.close()

main()
