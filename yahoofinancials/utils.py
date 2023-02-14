def remove_prefix(s, prefix):
    return s[len(prefix):] if s.startswith(prefix) else s


def get_request_config(tech_type, req_map):
    if tech_type == '':
        r_map = req_map['fundamentals']
    else:
        r_map = req_map['quoteSummary']
    return r_map


def get_request_category(tech_type, fin_types, statement_type):
    if tech_type == '':
        r_cat = fin_types.get(statement_type, [])[0]
    else:
        r_cat = tech_type
    return r_cat
