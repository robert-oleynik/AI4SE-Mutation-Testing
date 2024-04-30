local parser = vim.treesitter.get_parser(0)
local root = parser:parse()[1]:root()

local q = [[
(class_declaration
	body: (class_body (_
		(modifiers
			(marker_annotation
				name: (identifier) @ident.builtin
					(#eq? @ident.builtin "Mutation")))) @target))
]]
local query = vim.treesitter.query.parse("java", q)

for id, node, metadata in query:iter_captures(root, 0) do
	if id == 2 then
		print(vim.inspect(node))
		local r0, c0, r1, c1 = node:range()
		print(id, node:type(), string.format("%s:%s", r0, c0), "to", string.format("%s:%s", r1, c1))
	end
end
