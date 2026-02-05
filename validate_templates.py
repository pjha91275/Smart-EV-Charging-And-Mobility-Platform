from jinja2 import Environment, FileSystemLoader, TemplateSyntaxError

env = Environment(loader=FileSystemLoader('templates'))
templates = [
    'chat_interface.html',
    'user_insights.html',
    'nl_search.html',
    'station_analytics.html',
    'user_dashboard.html'
]

print("Validating Jinja2 templates...")
all_valid = True
for template_name in templates:
    try:
        env.get_template(template_name)
        print(f"✓ {template_name}")
    except TemplateSyntaxError as e:
        print(f"✗ {template_name}: {e}")
        all_valid = False
    except Exception as e:
        print(f"✗ {template_name}: {e}")
        all_valid = False

if all_valid:
    print("\n✓ All templates are valid!")
else:
    print("\n✗ Some templates have errors")
