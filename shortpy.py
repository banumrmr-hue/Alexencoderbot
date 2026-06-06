from python_minifier import minify


def run_shortpy(source_code: str) -> str:
    return minify(
        source_code,
        remove_literal_statements=True,
        remove_annotations=True,
        remove_pass=True,
        remove_asserts=True,
        remove_debug=True,
        remove_explicit_return_none=True,
        remove_object_base=True,
        combine_imports=True,
        hoist_literals=False,
        rename_globals=True,
        rename_locals=True,
        preserve_shebang=True,
    )
