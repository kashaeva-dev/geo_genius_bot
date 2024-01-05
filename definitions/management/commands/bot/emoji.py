import re

from definitions.models import Definition

async def replace_with_emoji(match):
    id = match.group(1)
    definition = await Definition.objects.aget(pk=id)
    return definition.emoji


async def async_re_sub(pattern, repl, string):
    matches = list(re.finditer(pattern, string))
    if not matches:
        return string

    last_end = 0
    result_parts = []
    for match in matches:
        start, end = match.span()
        result_parts.append(string[last_end:start])
        replacement = await repl(match)
        result_parts.append(replacement)
        last_end = end

    result_parts.append(string[last_end:])
    return ''.join(result_parts)
