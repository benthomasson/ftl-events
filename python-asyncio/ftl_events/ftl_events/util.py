
def get_modules(rulesets):

    modules = []

    for ruleset in rulesets:
        for rule in ruleset.rules:
            modules.append(rule.action.module)

    return list(set(modules))
