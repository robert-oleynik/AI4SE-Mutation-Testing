package de.hpi.ai4se.mutations;

import java.io.IOException;
import java.nio.file.DirectoryStream;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.List;

import lombok.Getter;

public class JavaFileScanner {
	@Getter
	private List<Source> sources;

	public JavaFileScanner() {
		this.sources = new ArrayList<>();
	}

	/**
	 *	@brief Recursively scans source root for .java files and add these to internal file store.
	 *
	 *	@param root Source root to scan for Java source files.
	 */
	public void scanRoot(Path sourceRoot) throws IOException {
		try(DirectoryStream<Path> stream = Files.newDirectoryStream(sourceRoot)) {
			for (Path path : stream) {
				if (Files.isDirectory(path)) {
					this.scanRoot(sourceRoot, path);
				} else if (path.toString().endsWith(".java")) {
					this.sources.add(new Source(sourceRoot, path));
				}
			}
		}
	}

	public void scanRoot(Path sourceRoot, Path subdir) throws IOException {}
}
