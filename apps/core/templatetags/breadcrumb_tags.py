from django import template
from django.urls import resolve, reverse
from django.urls.exceptions import Resolver404

register = template.Library()


@register.simple_tag(takes_context=True)
def breadcrumb(context):
    """
    Generate breadcrumbs automatically or use custom breadcrumbs from context.

    If 'custom_breadcrumbs' is present in the context, use those instead of
    auto-generating breadcrumbs from the URL path.

    Returns:
        list: List of breadcrumb dictionaries with 'title', 'url', and 'is_active' keys.
    """
    # Check if custom breadcrumbs are provided in context
    if "custom_breadcrumbs" in context:
        return context["custom_breadcrumbs"]

    request = context["request"]
    breadcrumbs = [
        {
            "title": "Dashboard",
            "url": "/dashboard/",
            "is_active": request.path == reverse("apps.dashboard:index"),
        }
    ]
    path_parts = request.path.split("/")
    current_path = f"/{path_parts[1]}/"

    for part in path_parts[2:]:
        if part:
            current_path += f"{part}/"
            try:
                url_name = resolve(current_path).url_name
                title = url_name.replace("_", " ").title()
                breadcrumbs.append(
                    {
                        "title": title,
                        "url": current_path,
                        "is_active": current_path == request.path,
                    }
                )
            except Resolver404:
                pass

    return breadcrumbs
