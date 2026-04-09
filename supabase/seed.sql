-- =====================================================================
-- Seed data for local dev — data sources + sample categories
-- =====================================================================

INSERT INTO public.data_sources (name, source_type, base_url, status, config) VALUES
    ('IEEE Xplore',      'api',     'https://ieeexploreapi.ieee.org/api/v1/search/articles', 'active', '{"rate_limit": 1.0, "max_papers": 5000}'),
    ('arXiv',            'api',     'http://export.arxiv.org/api/query',                     'active', '{"rate_limit": 3.0, "max_papers": 10000, "categories": ["cs.AI","cs.CL","cs.IR","cs.LG","cs.SE"]}'),
    ('ACM Digital Lib',  'scraper', 'https://dl.acm.org',                                    'active', '{"rate_limit": 0.5, "max_papers": 3000}'),
    ('SLIIT Repository', 'scraper', 'https://digital.lib.sliit.lk',                          'active', '{"rate_limit": 1.0, "max_papers": 1000}'),
    ('Google Scholar',   'scraper', 'https://scholar.google.com',                            'active', '{"rate_limit": 0.5, "max_papers": 2000}'),
    ('Semantic Scholar', 'api',     'https://api.semanticscholar.org/graph/v1',              'active', '{"rate_limit": 5.0, "max_papers": 5000}')
ON CONFLICT (name) DO NOTHING;
