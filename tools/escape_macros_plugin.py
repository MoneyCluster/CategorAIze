import re
from mkdocs.plugins import BasePlugin


class EscapeMacrosInCodePlugin(BasePlugin):
    """
    MkDocs plugin to escape {{ }} inside code blocks before macros plugin processes them.
    This prevents mkdocs-macros from evaluating macros that appear as examples in code.
    Runs before macros plugin due to plugin order in mkdocs.yml.
    """

    def on_page_markdown(self, markdown: str, **kwargs) -> str:
        """
        Process markdown before macros plugin runs.
        Replace {{ }} inside code blocks with placeholders so macros plugin doesn't process them.
        """
        # Match fenced code blocks (```language\n...```)
        FENCED_BLOCK_RE = re.compile(r"(```[^\n]*\n[\s\S]*?```)")
        # Match inline code spans (`...`)
        INLINE_CODE_RE = re.compile(r"`([^`\n]+)`")
        
        # Replace {{ }} with placeholders that macros won't recognize
        # Use unique markers that won't conflict
        def replace_in_fenced(match: re.Match) -> str:
            code_block = match.group(1)
            # Replace {{ with placeholder (something macros won't recognize)
            code_block = code_block.replace("{{", "╔╗╔╗")  # Double curly open
            code_block = code_block.replace("}}", "╚╝╚╝")  # Double curly close
            return code_block
        
        def replace_in_inline(match: re.Match) -> str:
            code_content = match.group(1)
            code_content = code_content.replace("{{", "╔╗╔╗")
            code_content = code_content.replace("}}", "╚╝╚╝")
            return f"`{code_content}`"
        
        # Process fenced blocks first, then inline
        temp_markdown = FENCED_BLOCK_RE.sub(replace_in_fenced, markdown)
        temp_markdown = INLINE_CODE_RE.sub(replace_in_inline, temp_markdown)
        
        return temp_markdown
    
    def on_page_content(self, html: str, **kwargs) -> str:
        """
        Restore placeholders back to {{ }} in HTML after markdown conversion.
        """
        # Restore placeholders in HTML code blocks
        html = html.replace("╔╗╔╗", "{{")
        html = html.replace("╚╝╚╝", "}}")
        return html
