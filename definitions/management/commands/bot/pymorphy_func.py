import pymorphy3


def get_accs_forms(word, axillary_word):
    morph = pymorphy3.MorphAnalyzer()
    word_parsed = morph.parse(word)[0]
    word_case = word_parsed.tag.case
    word_gender = word_parsed.tag.gender
    word_accs_form = word_parsed.inflect({'accs'}).word
    axillary_word_accs_form = morph.parse(axillary_word)[0].inflect({word_case, word_gender}).word
    return word_accs_form, axillary_word_accs_form
