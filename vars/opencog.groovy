def merge_parameters(params, additional) {
    merged = []
    params.each{ key, val ->
        merged.add(string(name: key, value: val))
    }
    merged.addAll(additional)
    return merged
}
