"""
Output formatters for the Writing Agent.

Converts newsletter content to various formats:
- HTML (blog-style with styling)
- Email HTML (responsive email template)
- Plain text
- Markdown
"""
import re
from typing import Dict, Any, Optional
from datetime import datetime, timezone


def format_html(
    content: str,
    title: str = "Newsletter",
    subtitle: Optional[str] = None,
) -> str:
    """
    Format newsletter content as blog-style HTML.

    Args:
        content: Markdown-formatted newsletter content
        title: Newsletter title
        subtitle: Optional subtitle or date

    Returns:
        HTML string with embedded styles
    """
    # Convert markdown to HTML
    html_content = _markdown_to_html(content)

    subtitle_html = f'<p class="subtitle">{subtitle}</p>' if subtitle else ""

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            background: #f9fafb;
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 40px 30px;
            border-radius: 12px;
            margin-bottom: 30px;
        }}
        .header h1 {{
            font-size: 2rem;
            margin-bottom: 10px;
        }}
        .subtitle {{
            opacity: 0.9;
            font-size: 1.1rem;
        }}
        .content {{
            background: white;
            padding: 30px;
            border-radius: 12px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.05);
        }}
        h2 {{
            color: #667eea;
            margin-top: 30px;
            margin-bottom: 15px;
            padding-bottom: 10px;
            border-bottom: 2px solid #f0f0f0;
        }}
        h3 {{
            color: #444;
            margin-top: 25px;
            margin-bottom: 10px;
        }}
        p {{
            margin-bottom: 15px;
        }}
        blockquote {{
            border-left: 4px solid #667eea;
            padding-left: 20px;
            margin: 20px 0;
            color: #555;
            font-style: italic;
            background: #f8f9ff;
            padding: 15px 20px;
            border-radius: 0 8px 8px 0;
        }}
        ul, ol {{
            margin: 15px 0;
            padding-left: 25px;
        }}
        li {{
            margin-bottom: 8px;
        }}
        strong {{
            color: #333;
        }}
        a {{
            color: #667eea;
            text-decoration: none;
        }}
        a:hover {{
            text-decoration: underline;
        }}
        .footer {{
            text-align: center;
            padding: 20px;
            color: #888;
            font-size: 0.9rem;
            margin-top: 30px;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>{title}</h1>
        {subtitle_html}
    </div>
    <div class="content">
        {html_content}
    </div>
    <div class="footer">
        <p>Generated with AI assistance</p>
    </div>
</body>
</html>"""


def format_email_html(
    content: str,
    title: str = "Newsletter",
    preheader: str = "",
    unsubscribe_url: str = "#",
) -> str:
    """
    Format newsletter content as responsive email HTML.

    Uses tables for email client compatibility.

    Args:
        content: Markdown-formatted newsletter content
        title: Newsletter title
        preheader: Preview text for email clients
        unsubscribe_url: Unsubscribe link URL

    Returns:
        Email-compatible HTML string
    """
    html_content = _markdown_to_html(content)
    date_str = datetime.now(timezone.utc).strftime("%B %d, %Y")

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta http-equiv="X-UA-Compatible" content="IE=edge">
    <title>{title}</title>
    <!--[if mso]>
    <style type="text/css">
        table {{border-collapse: collapse;}}
        .fallback-font {{font-family: Arial, sans-serif;}}
    </style>
    <![endif]-->
    <style>
        @media only screen and (max-width: 600px) {{
            .container {{
                width: 100% !important;
            }}
            .content-padding {{
                padding: 20px !important;
            }}
        }}
    </style>
</head>
<body style="margin: 0; padding: 0; background-color: #f4f4f4; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Arial, sans-serif;">
    <!-- Preheader -->
    <div style="display: none; max-height: 0; overflow: hidden;">
        {preheader}
    </div>

    <!-- Main Container -->
    <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0" style="background-color: #f4f4f4;">
        <tr>
            <td align="center" style="padding: 20px 10px;">
                <table role="presentation" class="container" width="600" cellspacing="0" cellpadding="0" border="0" style="background-color: #ffffff; border-radius: 8px; overflow: hidden;">
                    <!-- Header -->
                    <tr>
                        <td style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 30px; text-align: center;">
                            <h1 style="color: #ffffff; margin: 0; font-size: 24px; font-weight: bold;">{title}</h1>
                            <p style="color: rgba(255,255,255,0.9); margin: 10px 0 0 0; font-size: 14px;">{date_str}</p>
                        </td>
                    </tr>

                    <!-- Content -->
                    <tr>
                        <td class="content-padding" style="padding: 30px;">
                            {html_content}
                        </td>
                    </tr>

                    <!-- Footer -->
                    <tr>
                        <td style="background-color: #f8f9fa; padding: 20px; text-align: center; border-top: 1px solid #eee;">
                            <p style="color: #888; font-size: 12px; margin: 0;">
                                You received this email because you subscribed to our newsletter.
                                <br>
                                <a href="{unsubscribe_url}" style="color: #667eea;">Unsubscribe</a>
                            </p>
                        </td>
                    </tr>
                </table>
            </td>
        </tr>
    </table>
</body>
</html>"""


def format_plain_text(
    content: str,
    title: str = "Newsletter",
    width: int = 72,
) -> str:
    """
    Format newsletter content as plain text.

    Args:
        content: Markdown-formatted newsletter content
        title: Newsletter title
        width: Maximum line width

    Returns:
        Plain text string
    """
    # Remove markdown formatting
    text = content

    # Convert headers to plain text with underlines
    text = re.sub(r'^## (.+)$', r'\n\1\n' + '=' * 40, text, flags=re.MULTILINE)
    text = re.sub(r'^### (.+)$', r'\n\1\n' + '-' * 30, text, flags=re.MULTILINE)

    # Convert bold/italic
    text = re.sub(r'\*\*(.+?)\*\*', r'\1', text)
    text = re.sub(r'\*(.+?)\*', r'\1', text)

    # Convert blockquotes
    text = re.sub(r'^> (.+)$', r'  "\1"', text, flags=re.MULTILINE)

    # Convert bullet points
    text = re.sub(r'^- (.+)$', r'  • \1', text, flags=re.MULTILINE)

    # Convert links
    text = re.sub(r'\[(.+?)\]\((.+?)\)', r'\1 (\2)', text)

    # Wrap lines
    lines = []
    for line in text.split('\n'):
        if len(line) <= width:
            lines.append(line)
        else:
            words = line.split()
            current_line = ""
            for word in words:
                if len(current_line) + len(word) + 1 <= width:
                    current_line += (" " if current_line else "") + word
                else:
                    lines.append(current_line)
                    current_line = word
            if current_line:
                lines.append(current_line)

    date_str = datetime.now(timezone.utc).strftime("%B %d, %Y")

    header = f"""
{'=' * width}
{title.center(width)}
{date_str.center(width)}
{'=' * width}
"""

    footer = f"""
{'-' * width}
Generated with AI assistance
{'-' * width}
"""

    return header + '\n'.join(lines) + footer


def format_markdown(
    content: str,
    title: str = "Newsletter",
    include_metadata: bool = True,
) -> str:
    """
    Format newsletter content as clean Markdown.

    Args:
        content: Newsletter content (already in markdown)
        title: Newsletter title
        include_metadata: Whether to include YAML frontmatter

    Returns:
        Markdown string
    """
    date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    if include_metadata:
        frontmatter = f"""---
title: "{title}"
date: {date_str}
generated: true
---

"""
    else:
        frontmatter = ""

    header = f"# {title}\n\n"

    return frontmatter + header + content


def format_all(
    content: str,
    title: str = "Newsletter",
    subtitle: Optional[str] = None,
    preheader: Optional[str] = None,
) -> Dict[str, str]:
    """
    Generate all format versions of the newsletter.

    Args:
        content: Markdown-formatted newsletter content
        title: Newsletter title
        subtitle: Optional subtitle
        preheader: Optional email preheader text

    Returns:
        Dict with keys: html, email_html, text, markdown
    """
    return {
        "html": format_html(content, title, subtitle),
        "email_html": format_email_html(
            content,
            title,
            preheader or subtitle or "",
        ),
        "text": format_plain_text(content, title),
        "markdown": format_markdown(content, title),
    }


def _markdown_to_html(content: str) -> str:
    """
    Convert markdown content to HTML.

    Simple conversion for newsletter content.
    For complex markdown, consider using a library like markdown2.

    Args:
        content: Markdown string

    Returns:
        HTML string
    """
    html = content

    # Escape HTML entities first
    html = html.replace("&", "&amp;")
    html = html.replace("<", "&lt;")
    html = html.replace(">", "&gt;")

    # Restore blockquotes (we escaped > earlier)
    html = re.sub(r'^&gt; (.+)$', r'<blockquote>\1</blockquote>', html, flags=re.MULTILINE)

    # Headers
    html = re.sub(r'^### (.+)$', r'<h3>\1</h3>', html, flags=re.MULTILINE)
    html = re.sub(r'^## (.+)$', r'<h2>\1</h2>', html, flags=re.MULTILINE)
    html = re.sub(r'^# (.+)$', r'<h1>\1</h1>', html, flags=re.MULTILINE)

    # Bold and italic
    html = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', html)
    html = re.sub(r'\*(.+?)\*', r'<em>\1</em>', html)

    # Links
    html = re.sub(r'\[(.+?)\]\((.+?)\)', r'<a href="\2">\1</a>', html)

    # Bullet lists
    html = re.sub(r'^- (.+)$', r'<li>\1</li>', html, flags=re.MULTILINE)
    html = re.sub(r'(<li>.*</li>\n?)+', r'<ul>\g<0></ul>', html)

    # Paragraphs
    paragraphs = []
    current_para = []

    for line in html.split('\n'):
        line = line.strip()
        if not line:
            if current_para:
                para_text = ' '.join(current_para)
                if not para_text.startswith('<'):
                    para_text = f'<p>{para_text}</p>'
                paragraphs.append(para_text)
                current_para = []
        elif line.startswith('<h') or line.startswith('<ul') or line.startswith('<blockquote'):
            if current_para:
                para_text = ' '.join(current_para)
                if not para_text.startswith('<'):
                    para_text = f'<p>{para_text}</p>'
                paragraphs.append(para_text)
                current_para = []
            paragraphs.append(line)
        else:
            current_para.append(line)

    if current_para:
        para_text = ' '.join(current_para)
        if not para_text.startswith('<'):
            para_text = f'<p>{para_text}</p>'
        paragraphs.append(para_text)

    return '\n'.join(paragraphs)
