def define_env(env):
    def _rel_root(page_url: str) -> str:
        if not page_url:
            return ""
        # ensure trailing slash and compute depth
        url = page_url if page_url.endswith('/') else page_url + '/'
        # remove leading slash if any
        if url.startswith('/'):
            url = url[1:]
        # count segments excluding the empty last due to trailing slash
        segments = [s for s in url.split('/') if s]
        depth = len(segments)
        return "../" * depth

    def likec4_iframe(path: str = "", height: str = "70vh") -> str:
        base = "/_static/likec4/"
        if getattr(env, 'page', None) and getattr(env.page, 'url', None):
            base = f"{_rel_root(env.page.url)}_static/likec4/"
        src = f"{base}{path.strip('/')}/" if path else f"{base}"
        return (
            f'<div style="height:{height}">\n'
            f'  <iframe src="{src}" title="LikeC4" style="width:100%; height:100%; border:0"></iframe>\n'
            f'</div>'
        )

    env.macro(likec4_iframe)

    def likec4_view(project: str, view: str = "landscape", height: str = "70vh") -> str:
        # LikeC4 uses hash-based routing for views
        # Format: index.html#project/ProjectName/views/viewName
        # Always use absolute path from site root - works consistently on all pages
        base = None
        try:
            base = env.conf.get('extra', {}).get('likec4_host')
        except Exception:
            base = None
        
        # Get site_url base path (e.g., /CategorAIze/ for GitHub Pages)
        site_base = ""
        try:
            site_url = env.conf.get('site_url', '').rstrip('/')
            if site_url:
                from urllib.parse import urlparse
                parsed = urlparse(site_url)
                site_base = parsed.path.rstrip('/')
        except Exception:
            pass
        
        if not base:
            # Use absolute path from site root
            src = f"{site_base}/_static/likec4/index.html"
        else:
            src = f"{base.rstrip('/')}/index.html"
        
        hash_route = f"project/{project}/views/{view}"
        iframe_id = f"likec4-{project}-{view}".replace(" ", "-").lower()
        return (
            f'<div style="height:{height}">\n'
            f'  <iframe id="{iframe_id}" src="{src}#{hash_route}" title="LikeC4" style="width:100%; height:100%; border:0"></iframe>\n'
            f'</div>'
        )

    env.macro(likec4_view)


