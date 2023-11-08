from django import template
register = template.Library()

@register.filter
def add_commas(value):
    try:
        return "{:,}".format(int(value))
    except ValueError:
        return value  # intに変換できない場合はそのままの値を返す
