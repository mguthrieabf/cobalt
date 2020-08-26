from django import template
from django.utils.dateformat import DateFormat

register = template.Library()

# custom filter for datetime so we can get "am" amd "pm" instead of "a.m." and "p.m."
# accepted datetime object or time object
# returns e.g. 10am, 7:15pm 10:01am
@register.filter(name="cobalt_time", expects_localtime=True)
def cobalt_time(value):

    hour_str = value.strftime("%I")
    min_str = value.strftime("%M")
    ampm_str = value.strftime("%p").replace(".", "").lower()
    hour_num = "%d" % int(hour_str)

    if min_str == "00":
        time_str = f"{hour_num}{ampm_str}"
    else:
        time_str = f"{hour_num}:{min_str}{ampm_str}"

    return time_str


# custom filter for datetime to format as full date
@register.filter(name="cobalt_nice_date", expects_localtime=True)
def cobalt_nice_date(value):

    return DateFormat(value).format("l jS M Y")


# custom filter for datetime to format as full date
@register.filter(name="cobalt_nice_datetime", expects_localtime=True)
def cobalt_nice_datetime(value):

    date_part = cobalt_nice_date(value)
    time_part = cobalt_time(value)

    return f"{date_part} {time_part}"
