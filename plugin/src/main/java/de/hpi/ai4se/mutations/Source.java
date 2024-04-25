package de.hpi.ai4se.mutations;

import java.nio.file.Path;

import lombok.Getter;

public class Source {
	@Getter
	Path sourceRoot;
	@Getter
	Path sourceFile;

	public Source(Path sourceRoot, Path sourcePath) {
		this.sourceRoot = sourceRoot;
		this.sourceFile = sourcePath.relativize(sourceRoot);
	}
}
