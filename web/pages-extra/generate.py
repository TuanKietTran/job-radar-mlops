import html
import json
from pathlib import Path

BASE = 'https://job-radar.example'
LASTMOD = '2026-11-14'
ROOT = Path(__file__).resolve().parent
DATA = ROOT / 'data' / 'companies.json'
SITE = ROOT / 'site'

INDUSTRY_NOTES = {
    'software development': 'Software firms in this directory build business tools, booking systems and internal software for other small and mid-size firms.',
    'financial technology': 'Financial technology firms in this directory build payment, lending and bookkeeping tools for small businesses and market vendors.',
    'e-commerce': 'E-commerce firms in this directory run storefront and marketplace services for sellers of crafts, groceries and second-hand goods.',
    'logistics': 'Logistics firms in this directory build route, warehouse and freight booking tools for delivery teams and trucking firms.',
    'health technology': 'Health technology firms in this directory build scheduling, intake and records software for clinics.',
    'education technology': 'Education technology firms in this directory build course, exam and attendance tools for schools and training centres.',
    'manufacturing': 'Manufacturing firms in this directory build stock, order and maintenance software for small factories and food processors.',
    'agriculture technology': 'Agriculture technology firms in this directory build crop, soil and harvest planning tools for growers and cooperatives.',
    'renewable energy': 'Renewable energy firms in this directory build meter reading, billing and usage tools for solar installers and owners.',
    'hospitality technology': 'Hospitality technology firms in this directory build booking and front desk tools for hotels, guesthouses and tour operators.',
}

CITY_NOTES = {
    'Ho Chi Minh City': 'Firms based in Ho Chi Minh City in this directory cover software, logistics and hospitality work.',
    'Hanoi': 'Firms based in Hanoi in this directory cover software, finance and manufacturing work.',
    'Da Nang': 'Firms based in Da Nang in this directory work on software, tourism bookings and clinic tools.',
    'Hai Phong': 'Firms based in Hai Phong in this directory work on port logistics, warehousing and factory software.',
    'Can Tho': 'Firms based in Can Tho in this directory work on farming tools, groceries and logistics.',
    'Nha Trang': 'Firms based in Nha Trang in this directory work on hotel bookings, tour tools and small retail software.',
    'Hue': 'Firms based in Hue in this directory build school, clinic and guesthouse software.',
    'Da Lat': 'Firms based in Da Lat in this directory work on farm planning, guesthouse bookings and small retail tools.',
    'Binh Duong': 'Firms based in Binh Duong in this directory work on factory stock, maintenance and payroll software.',
    'Dong Nai': 'Firms based in Dong Nai in this directory work on food processing, factory and logistics software.',
}


def esc(text):
    return html.escape(str(text), quote=True)


def slugify(text):
    return text.lower().replace(' ', '-')


def page(title, description, canonical, body):
    lines = []
    lines.append('<!doctype html>')
    lines.append('<html lang=\'en\'>')
    lines.append('<head>')
    lines.append('<meta charset=\'utf-8\'>')
    lines.append('<meta name=\'viewport\' content=\'width=device-width, initial-scale=1\'>')
    lines.append('<title>' + esc(title) + '</title>')
    lines.append('<meta name=\'description\' content=\'' + esc(description) + '\'>')
    lines.append('<link rel=\'canonical\' href=\'' + BASE + canonical + '\'>')
    lines.append('<meta property=\'og:title\' content=\'' + esc(title) + '\'>')
    lines.append('<meta property=\'og:description\' content=\'' + esc(description) + '\'>')
    lines.append('<meta property=\'og:type\' content=\'website\'>')
    lines.append('</head>')
    lines.append('<body>')
    lines.append('<nav><a href=\'/\'>Company directory</a></nav>')
    lines.append('<main>')
    lines.append(body)
    lines.append('</main>')
    lines.append('</body>')
    lines.append('</html>')
    return '\n'.join(lines) + '\n'


def company_link(company):
    return '<li><a href=\'/companies/' + company['slug'] + '.html\'>' + esc(company['name']) + '</a> - ' + esc(company['industry'].title()) + ', ' + esc(company['city']) + ' - ' + str(company['open_roles']) + ' open roles</li>'


def write(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding='utf-8')


def main():
    companies = json.loads(DATA.read_text(encoding='utf-8'))
    companies = sorted(companies, key=lambda c: c['name'])
    industries = sorted({c['industry'] for c in companies})
    cities = sorted({c['city'] for c in companies})
    pages = []
    index_items = '\n'.join(company_link(c) for c in companies)
    industry_links = '\n'.join('<li><a href=\'/industries/' + slugify(i) + '.html\'>' + esc(i.title()) + '</a></li>' for i in industries)
    city_links = '\n'.join('<li><a href=\'/cities/' + slugify(c) + '.html\'>' + esc(c) + '</a></li>' for c in cities)
    index_body = '<h1>Company directory</h1>\n<p>Forty invented companies listed in this directory, grouped by industry and city.</p>\n<h2>Browse by industry</h2>\n<ul>\n' + industry_links + '\n</ul>\n<h2>Browse by city</h2>\n<ul>\n' + city_links + '\n</ul>\n<h2>All companies</h2>\n<ul>\n' + index_items + '\n</ul>'
    write(SITE / 'index.html', page('Company directory', 'Browse forty invented companies by industry and city.', '/', index_body))
    pages.append('/')
    for company in companies:
        industry_slug = slugify(company['industry'])
        city_slug = slugify(company['city'])
        body = '<h1>' + esc(company['name']) + '</h1>\n<p>' + esc(company['description']) + '</p>\n<h2>Details</h2>\n<dl>\n<dt>Industry</dt><dd><a href=\'/industries/' + industry_slug + '.html\'>' + esc(company['industry'].title()) + '</a></dd>\n<dt>City</dt><dd><a href=\'/cities/' + city_slug + '.html\'>' + esc(company['city']) + '</a></dd>\n<dt>Size</dt><dd>' + esc(company['size']) + ' people</dd>\n<dt>Founded</dt><dd>' + str(company['founded']) + '</dd>\n</dl>\n<h2>Open roles</h2>\n<p>' + str(company['open_roles']) + ' open roles listed.</p>'
        path = '/companies/' + company['slug'] + '.html'
        write(SITE / path.lstrip('/'), page(company['name'], company['description'], path, body))
        pages.append(path)
    for industry in industries:
        matching = [c for c in companies if c['industry'] == industry]
        total = sum(c['open_roles'] for c in matching)
        items = '\n'.join(company_link(c) for c in matching)
        body = '<h1>' + esc(industry.title()) + ' companies</h1>\n<p>' + esc(INDUSTRY_NOTES[industry]) + '</p>\n<p>' + str(len(matching)) + ' companies, ' + str(total) + ' open roles in total.</p>\n<h2>Companies</h2>\n<ul>\n' + items + '\n</ul>'
        path = '/industries/' + slugify(industry) + '.html'
        write(SITE / path.lstrip('/'), page(industry.title() + ' companies', INDUSTRY_NOTES[industry], path, body))
        pages.append(path)
    for city in cities:
        matching = [c for c in companies if c['city'] == city]
        total = sum(c['open_roles'] for c in matching)
        items = '\n'.join(company_link(c) for c in matching)
        body = '<h1>Companies in ' + esc(city) + '</h1>\n<p>' + esc(CITY_NOTES[city]) + '</p>\n<p>' + str(len(matching)) + ' companies, ' + str(total) + ' open roles in total.</p>\n<h2>Companies</h2>\n<ul>\n' + items + '\n</ul>'
        path = '/cities/' + slugify(city) + '.html'
        write(SITE / path.lstrip('/'), page('Companies in ' + city, CITY_NOTES[city], path, body))
        pages.append(path)
    url_entries = '\n'.join('<url><loc>' + BASE + p + '</loc><lastmod>' + LASTMOD + '</lastmod></url>' for p in sorted(pages))
    sitemap = '<?xml version=\'1.0\' encoding=\'UTF-8\'?>\n<urlset xmlns=\'http://www.sitemaps.org/schemas/sitemap/0.9\'>\n' + url_entries + '\n</urlset>\n'
    write(SITE / 'sitemap.xml', sitemap)
    write(SITE / 'robots.txt', 'User-agent: *\nAllow: /\nSitemap: ' + BASE + '/sitemap.xml\n')
    print('generated: 1 index, ' + str(len(companies)) + ' company pages, ' + str(len(industries)) + ' industry pages, ' + str(len(cities)) + ' city pages')


if __name__ == '__main__':
    main()
