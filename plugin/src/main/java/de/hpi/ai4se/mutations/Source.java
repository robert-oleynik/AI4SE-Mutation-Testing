package de.hpi.ai4se.mutations;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.List;

import org.treesitter.*;

import lombok.Builder;
import lombok.Getter;

public class Source {
	@Getter
	Path sourceRoot;
	@Getter
	Path sourceFile;

	// NOTE: (#eq?) does not work
	private static final String TS_TARGET_QUERY = "(class_declaration body: (class_body (_ (modifiers (marker_annotation name: (identifier) @ident.builtin))) @target))";

	@Builder
	public static class MutationTarget {
		@Getter String content;
		@Getter int begin;
		@Getter int end;
	}

	public Source(Path sourceRoot, Path sourcePath) {
		this.sourceRoot = sourceRoot;
		this.sourceFile = sourceRoot.relativize(sourcePath);
	}

	public List<String> identifyMutations() throws IOException {
		Path path = this.sourceRoot.resolve(this.sourceFile);
		// TODO: Encoding
		String content = Files.readString(path);

		TSParser parser = new TSParser();
		TSLanguage lang = new TreeSitterJava();
		parser.setLanguage(lang);

		TSTree tree = parser.parseString(null, content);
		TSNode root = tree.getRootNode();
		TSQuery query = new TSQuery(lang, TS_TARGET_QUERY);
		TSQueryCursor cursor = new TSQueryCursor();
		cursor.exec(query, root);

		List<String> list = new ArrayList<String>();
		TSQueryMatch match = new TSQueryMatch();
		while (cursor.nextMatch(match)) {
			TSQueryCapture[] captures = match.getCaptures();
			TSNode node = captures[0].getNode();
			TSNode ident = captures[1].getNode();
			int begin = ident.getStartByte();
			int end = ident.getEndByte();
			if (content.substring(begin, end) == "Mutate") {
				list.add(content.substring(node.getStartByte(), node.getEndByte()));
			}
		}
		return list;
	}
}
