def define_env(env):
    def likec4_iframe(path: str = "", height: str = "70vh") -> str:
        base = "../_static/likec4/" if env.page and env.page.url else "/_static/likec4/"
        src = f"{base}{path.strip('/')}/" if path else f"{base}"
        return (
            f'<div style="height:{height}">\n'
            f'  <iframe src="{src}" title="LikeC4" style="width:100%; height:100%; border:0"></iframe>\n'
            f'</div>'
        )

    env.macro(likec4_iframe)


