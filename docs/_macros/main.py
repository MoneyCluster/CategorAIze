def define_env(env):
    # Escape macros inside code blocks before macro expansion
    # Note: mkdocs-macros processes macros BEFORE markdown parsing,
    # so we need to escape {{ }} in code blocks manually
    import re
    
    def escape_macros_in_code_blocks(text: str) -> str:
        """
        Escape {{ }} patterns inside code blocks (``` blocks) before macro processing.
        This prevents macros from being processed when they appear as examples.
        """
        # Pattern to match fenced code blocks (```...```)
        # Match from opening ``` to closing ```, handling language tag and content
        code_block_pattern = r'(```[^\n]*\n[\s\S]*?```)'
        
        def escape_in_block(match):
            code_block = match.group(1)
            # Escape all {{ and }} inside the code block to HTML entities
            escaped = code_block.replace('{{', '&#123;&#123;').replace('}}', '&#125;&#125;')
            return escaped
        
        # Process all code blocks
        return re.sub(code_block_pattern, escape_in_block, text)
    
    # Store the function - we'll need to call it via a custom MkDocs plugin hook
    # For now, we register it as a variable so it can be used if needed
    if hasattr(env, 'variables'):
        env.variables['_escape_code_blocks'] = escape_macros_in_code_blocks
    
    # Note: mkdocs-macros doesn't have a built-in preprocessor hook that runs
    # before macro expansion for code blocks. The best approach is to manually
    # escape {{ }} in documentation examples (as we do in contributing.md)
    
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
        
        # With --use-hash-history, LikeC4 uses hash-based routing: #/view/{viewName}/
        # Format is different from non-hash mode
        hash_route = f"/view/{view}/"
        iframe_id = f"likec4-{project}-{view}".replace(" ", "-").lower()
        return (
            f'<div style="height:{height}">\n'
            f'  <iframe id="{iframe_id}" src="{src}#{hash_route}" title="LikeC4" style="width:100%; height:100%; border:0"></iframe>\n'
            f'</div>'
        )

    env.macro(likec4_view)


