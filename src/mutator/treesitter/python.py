import tree_sitter as ts
import tree_sitter_python as tsp

tsLang = ts.Language(tsp.language(), "python")
tsParser = ts.Parser()
tsParser.set_language(tsLang)
