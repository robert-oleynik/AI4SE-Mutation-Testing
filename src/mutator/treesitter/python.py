import tree_sitter as ts
import tree_sitter_python as tsp

tsLang = ts.Language(tsp.language())
tsParser = ts.Parser(tsLang)
