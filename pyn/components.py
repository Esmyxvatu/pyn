"""
File to define the Components.
Components are an easier way to create HTML, mapping it automatically to valid HTML.
"""


class Components:
    """
    Short way to create basic HTML in python.
    Usage : Components.<tagname>(<text>, <other data>)
    <tagname> : The element you want to create
    <text> : the text in the element
    <other data> : To define other thing, like id, class (use class_), etc
    """

    def __str__(self):
        return "Components element"

    def __getattr__(self, tag):
        single = [
            "br", 
            "hr", 
            "base", 
            "meta", 
            "input", 
            "col", 
            "link", 
            "area", 
            "track", 
            "source", 
            "img"
        ]

        def generate(*content, **attributes):
            attrs = " ".join(
                f'{k if k != "class_" else "class"}="{v}"'
                for k, v in attributes.items()
                )
            inner = "".join(content)
            return f"<{tag} {attrs}/>" if tag in single else f"<{tag} {attrs}>{inner}</{tag}>"
        return generate
