from extract import locales

KNOWN = {"en": {"Landslide", "Catapult"}, "zh-CN": {"地裂", "投石车"}}


def build(columns):
    keys = [f"Generated/hupg_item{n}_name" for n in range(len(columns[0]))]
    return {key: [column[row] for column in columns] for row, key in enumerate(keys)}


def test_english_and_chinese_identified_from_repo_evidence():
    records = build([["Landslide", "Catapult"], ["地裂", "投石车"]])
    labels, evidence = locales.identify_locales(records, KNOWN)
    assert labels[0] == "en"
    assert labels[1] == "zh-CN"
    assert evidence["en"]["basis"] == "repo"
    assert evidence["zh-CN"]["matched"] == 2


def test_unique_scripts_identified():
    records = build(
        [
            ["Landslide", "Catapult"],
            ["地裂", "投石车"],
            ["地滑り", "カタパルト"],
            ["산사태", "투석기"],
            ["ดินถล่ม", "เครื่องยิง"],
        ]
    )
    labels, evidence = locales.identify_locales(records, KNOWN)
    assert labels[2] == "ja"
    assert labels[3] == "ko"
    assert labels[4] == "th"
    assert evidence["ja"]["basis"] == "script"


def test_unprovable_latin_column_stays_positional():
    records = build([["Landslide", "Catapult"], ["Erdrutsch", "Katapult"]])
    labels, evidence = locales.identify_locales(records, KNOWN)
    assert labels[1] == "locale_01"
    assert evidence["locale_01"]["basis"] == "unresolved"
    assert evidence["locale_01"]["scriptHint"] == "latin"


def test_two_cyrillic_columns_are_not_guessed():
    records = build(
        [["Landslide", "Catapult"], ["Оползень", "Катапульта"], ["Зсув", "Катапульта"]]
    )
    labels, _ = locales.identify_locales(records, KNOWN)
    assert labels[1] == "locale_01"
    assert labels[2] == "locale_02"


def test_second_chinese_column_does_not_steal_the_label():
    records = build([["Landslide", "Catapult"], ["地裂", "投石车"], ["岩塌", "投石機"]])
    labels, _ = locales.identify_locales(records, KNOWN)
    assert labels[1] == "zh-CN"
    assert labels[2] == "locale_02"


def test_labels_are_unique():
    records = build([["Landslide", "Catapult"], ["地滑り", "カタパルト"], ["日本語", "テスト"]])
    labels, _ = locales.identify_locales(records, KNOWN)
    assert len(set(labels.values())) == len(labels)
