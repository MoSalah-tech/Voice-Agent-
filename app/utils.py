import re

def strip_markdown_for_speech(text: str) -> str:
    """
    Remove common Markdown formatting so TTS reads clean text.
    Keeps the main content but drops symbols like *, #, |, etc.
    """
    # Remove code blocks (```...```)
    text = re.sub(r'```.*?```', '', text, flags=re.DOTALL)
    # Remove inline code (`...`)
    text = re.sub(r'`([^`]*)`', r'\1', text)
    # Remove images ![alt](url) -> alt
    text = re.sub(r'!\[([^\]]*)\]\([^)]*\)', r'\1', text)
    # Remove links [text](url) -> text
    text = re.sub(r'\[([^\]]*)\]\([^)]*\)', r'\1', text)
    # Remove bold **text** and italic *text*
    text = re.sub(r'\*\*([^*]*)\*\*', r'\1', text)
    text = re.sub(r'\*([^*]*)\*', r'\1', text)
    # Remove underscores for bold/italic (__text__, _text_)
    text = re.sub(r'__([^_]*)__', r'\1', text)
    text = re.sub(r'_([^_]*)_', r'\1', text)
    # Remove headers (#, ##, ###)
    text = re.sub(r'#+\s*(.*)', r'\1', text)
    # Remove horizontal rules (---, ***, ___)
    text = re.sub(r'^\s*([-*_])\s*$', '', text, flags=re.MULTILINE)
    # Remove table pipes and alignment rows (| --- |)
    # First, remove table separator lines
    text = re.sub(r'^\s*\|?\s*[-:]+\s*\|?(\s*[-:]+\s*\|?)*\s*$', '', text, flags=re.MULTILINE)
    # Then replace pipe characters with spaces
    text = text.replace('|', ' ')
    # Remove bullet points (-, *, +) at start of lines, replace with space
    text = re.sub(r'^\s*[-*+]\s+', '', text, flags=re.MULTILINE)
    # Remove blockquote > at start
    text = re.sub(r'^\s*>\s?', '', text, flags=re.MULTILINE)
    # Collapse multiple spaces/newlines
    text = re.sub(r'\n{3,}', '\n\n', text)
    text = re.sub(r'[ \t]+', ' ', text)
    return text.strip()