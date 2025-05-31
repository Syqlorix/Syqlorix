def css(**rules):
    s = []
    for selector, styles in rules.items():
        s.append(f"{selector} {{")
        for prop, value in styles.items():
            s.append(f"  {prop.replace('_', '-')}: {value};")
        s.append("}")
    return "\n".join(s)